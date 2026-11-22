
import logging

import stripe

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.cart import Cart
from orders.models import Order
from reservations.models import Reservation

from notifications.services import (
    send_order_paid_notifications,
    send_reservation_paid_notifications,
)

from .services import (
    create_order_checkout_session,
    create_reservation_checkout_session,
    euros_to_cents,
    retrieve_checkout_session,
    expire_checkout_session,
)


logger = logging.getLogger(__name__)


# ==================================================
# ACCESS CONTROL
# ==================================================

def _owns_order(request, order):
    return (
        request.session.get("pending_order_id") == order.pk
        or request.session.get("last_order_id") == order.pk
    )


def _owns_reservation(request, reservation):
    return (
        request.session.get("last_reservation_id")
        == reservation.pk
    )


# ==================================================
# CHECKOUT SESSION VALIDATION
# ==================================================

def _session_matches(
    session,
    *,
    payment_type,
    object_id,
    amount,
):
    metadata = session.get("metadata") or {}

    identifier = (
        "order_id"
        if payment_type == "order"
        else "reservation_id"
    )

    return (
        session.get("mode") == "payment"
        and session.get("currency") == "eur"
        and session.get("amount_total")
        == euros_to_cents(amount)
        and metadata.get("payment_type") == payment_type
        and metadata.get(identifier) == str(object_id)
    )


def _session_is_paid(session):
    return (
        session.get("status") == "complete"
        and session.get("payment_status") == "paid"
    )


# ==================================================
# NOTIFICATIONS
# ==================================================

def _notify_order(order_id):
    try:
        order = Order.objects.get(pk=order_id)
        send_order_paid_notifications(order)
    except Exception:
        logger.exception(
            "Order #%s notification failure.",
            order_id,
        )


def _notify_reservation(reservation_id):
    try:
        reservation = Reservation.objects.get(
            pk=reservation_id
        )
        send_reservation_paid_notifications(reservation)
    except Exception:
        logger.exception(
            "Reservation #%s notification failure.",
            reservation_id,
        )


# ==================================================
# PAYMENT CONFIRMATION
# ==================================================

def _mark_order_paid(session):
    metadata = session.get("metadata") or {}
    order_id = metadata.get("order_id")

    if not order_id:
        return False

    try:
        with transaction.atomic():
            order = (
                Order.objects.select_for_update()
                .get(pk=order_id)
            )

            if order.is_paid:
                return (
                    order.payment_reference
                    == session.get("id")
                )

            if (
                order.payment_reference
                != session.get("id")
            ):
                return False

            if not _session_matches(
                session,
                payment_type="order",
                object_id=order.pk,
                amount=order.total,
            ):
                return False

            if not _session_is_paid(session):
                return False

            order.payment_status = (
                Order.PaymentStatus.PAID
            )
            order.amount_paid = order.total
            order.paid_at = timezone.now()

            order.save(
                update_fields=[
                    "payment_status",
                    "amount_paid",
                    "paid_at",
                ]
            )

            transaction.on_commit(
                lambda pk=order.pk: _notify_order(pk)
            )

        return True

    except (Order.DoesNotExist, ValueError, TypeError):
        return False


def _mark_reservation_paid(session):
    metadata = session.get("metadata") or {}
    reservation_id = metadata.get("reservation_id")

    if not reservation_id:
        return False

    try:
        with transaction.atomic():
            reservation = (
                Reservation.objects.select_for_update()
                .get(pk=reservation_id)
            )

            if reservation.deposit_is_paid:
                return (
                    reservation.deposit_reference
                    == session.get("id")
                )

            if (
                reservation.deposit_reference
                != session.get("id")
            ):
                return False

            if not _session_matches(
                session,
                payment_type="reservation",
                object_id=reservation.pk,
                amount=reservation.deposit_amount,
            ):
                return False

            if not _session_is_paid(session):
                return False

            reservation.deposit_status = (
                Reservation.DepositStatus.PAID
            )
            reservation.deposit_paid_at = timezone.now()

            reservation.save(
                update_fields=[
                    "deposit_status",
                    "deposit_paid_at",
                ]
            )

            transaction.on_commit(
                lambda pk=reservation.pk:
                    _notify_reservation(pk)
            )

        return True

    except (
        Reservation.DoesNotExist,
        ValueError,
        TypeError,
    ):
        return False


# ==================================================
# CHECKOUT LIFECYCLE
# ==================================================

def _get_or_create_checkout(
    request,
    *,
    model,
    pk,
    reference_field,
    paid_field,
    payment_type,
    amount_field,
    create_session,
):
    """
    Serialize Checkout creation using a database lock.

    An open matching session is reused.
    A completed paid session is never replaced.
    An expired session can be replaced.
    """

    with transaction.atomic():
        obj = (
            model.objects.select_for_update()
            .get(pk=pk)
        )

        if paid_field(obj):
            return None

        reference = getattr(obj, reference_field)
        amount = amount_field(obj)

        if reference:
            existing = retrieve_checkout_session(reference)

            if not _session_matches(
                existing,
                payment_type=payment_type,
                object_id=obj.pk,
                amount=amount,
            ):
                raise ValueError(
                    "Existing Checkout session does not "
                    "match the payment record."
                )

            if _session_is_paid(existing):
                raise ValueError(
                    "Payment already completed on Stripe. "
                    "Awaiting webhook confirmation."
                )

            if existing.get("status") == "open":
                if (
                    existing.get("payment_status")
                    == "unpaid"
                ):
                    return existing

                raise ValueError(
                    "Checkout is awaiting confirmation."
                )

            if existing.get("status") not in (
                "expired",
                "complete",
            ):
                raise ValueError(
                    "Unexpected Checkout status."
                )

            if existing.get("status") == "complete":
                raise ValueError(
                    "Completed Checkout requires review."
                )

        session = create_session(request, obj)

        setattr(obj, reference_field, session.id)
        obj.save(update_fields=[reference_field])

        return session


# ==================================================
# ORDER PAYMENT
# ==================================================

@require_POST
def order_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if not _owns_order(request, order):
        return redirect("orders:cart")

    if order.is_paid:
        request.session["last_order_id"] = order.pk
        return redirect(
            "orders:success",
            order_id=order.pk,
        )

    try:
        session = _get_or_create_checkout(
            request,
            model=Order,
            pk=order.pk,
            reference_field="payment_reference",
            paid_field=lambda obj: obj.is_paid,
            payment_type="order",
            amount_field=lambda obj: obj.total,
            create_session=create_order_checkout_session,
        )

    except (
        stripe.StripeError,
        ValueError,
    ):
        logger.exception(
            "Checkout unavailable for order #%s.",
            order.pk,
        )
        messages.error(
            request,
            (
                "Paiement indisponible ou en cours "
                "de confirmation. Veuillez patienter."
            ),
        )
        return redirect(
            "orders:payment",
            order_id=order.pk,
        )

    if session is None:
        return redirect(
            "orders:success",
            order_id=order.pk,
        )

    return redirect(session.url, code=303)


def order_success(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if not _owns_order(request, order):
        return redirect("orders:cart")

    session_id = request.GET.get("session_id")

    if session_id and session_id == order.payment_reference:
        try:
            session = retrieve_checkout_session(
                session_id
            )

            if not _session_matches(
                session,
                payment_type="order",
                object_id=order.pk,
                amount=order.total,
            ):
                logger.warning(
                    "Invalid order success session #%s.",
                    order.pk,
                )

        except (stripe.StripeError, ValueError):
            logger.exception(
                "Order Checkout retrieval failed."
            )

    order.refresh_from_db()

    if not order.is_paid:
        messages.info(
            request,
            (
                "Votre paiement est en cours de "
                "confirmation. Veuillez patienter."
            ),
        )
        return redirect(
            "orders:payment",
            order_id=order.pk,
        )

    Cart(request).clear()

    request.session["last_order_id"] = order.pk
    request.session.pop("pending_order_id", None)

    return redirect(
        "orders:success",
        order_id=order.pk,
    )


def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if not _owns_order(request, order):
        return redirect("orders:cart")

    if order.is_paid:
        request.session["last_order_id"] = order.pk
        return redirect(
            "orders:success",
            order_id=order.pk,
        )

    request.session["pending_order_id"] = order.pk

    messages.warning(
        request,
        (
            "Le paiement a été annulé. "
            "Votre commande reste en attente."
        ),
    )

    return redirect(
        "orders:payment",
        order_id=order.pk,
    )


# ==================================================
# RESERVATION PAYMENT
# ==================================================

@require_POST
def reservation_payment(request, pk):
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
    )

    if not _owns_reservation(request, reservation):
        return redirect("reservations:create")

    if reservation.deposit_is_paid:
        return redirect("reservations:success")

    try:
        session = _get_or_create_checkout(
            request,
            model=Reservation,
            pk=reservation.pk,
            reference_field="deposit_reference",
            paid_field=lambda obj: obj.deposit_is_paid,
            payment_type="reservation",
            amount_field=lambda obj: obj.deposit_amount,
            create_session=(
                create_reservation_checkout_session
            ),
        )

    except (
        stripe.StripeError,
        ValueError,
    ):
        logger.exception(
            "Reservation Checkout unavailable."
        )
        messages.error(
            request,
            (
                "Paiement indisponible ou en cours "
                "de confirmation. Veuillez patienter."
            ),
        )
        return redirect(
            "reservations:deposit",
            pk=reservation.pk,
        )

    if session is None:
        return redirect("reservations:success")

    return redirect(session.url, code=303)


def reservation_success(request, pk):
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
    )

    if not _owns_reservation(request, reservation):
        return redirect("reservations:create")

    session_id = request.GET.get("session_id")

    if (
        session_id
        and session_id == reservation.deposit_reference
    ):
        try:
            session = retrieve_checkout_session(
                session_id
            )

            if not _session_matches(
                session,
                payment_type="reservation",
                object_id=reservation.pk,
                amount=reservation.deposit_amount,
            ):
                logger.warning(
                    "Invalid reservation success session."
                )

        except (stripe.StripeError, ValueError):
            logger.exception(
                "Reservation Checkout retrieval failed."
            )

    reservation.refresh_from_db()

    if not reservation.deposit_is_paid:
        messages.info(
            request,
            (
                "Votre acompte est en cours de "
                "confirmation. Veuillez patienter."
            ),
        )
        return redirect(
            "reservations:deposit",
            pk=reservation.pk,
        )

    return redirect("reservations:success")


def reservation_cancel(request, pk):
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
    )

    if not _owns_reservation(request, reservation):
        return redirect("reservations:create")

    if reservation.deposit_is_paid:
        return redirect("reservations:success")

    messages.warning(
        request,
        (
            "Le paiement a été annulé. "
            "Votre réservation reste en attente "
            "du paiement de l’acompte."
        ),
    )

    return redirect(
        "reservations:deposit",
        pk=reservation.pk,
    )


# ==================================================
# STRIPE WEBHOOK
# ==================================================

@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error(
            "STRIPE_WEBHOOK_SECRET is not configured."
        )
        return HttpResponse(status=503)

    signature = request.META.get(
        "HTTP_STRIPE_SIGNATURE",
        "",
    )

    try:
        event = stripe.Webhook.construct_event(
            request.body,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )

    except (
        ValueError,
        stripe.error.SignatureVerificationError,
    ):
        return HttpResponse(status=400)

    if event["type"] != "checkout.session.completed":
        return HttpResponse(status=200)

    session = event["data"]["object"]

    if session.get("payment_status") != "paid":
        return HttpResponse(status=200)

    metadata = session.get("metadata") or {}
    payment_type = metadata.get("payment_type")

    try:
        if payment_type == "order":
            success = _mark_order_paid(session)

        elif payment_type == "reservation":
            success = _mark_reservation_paid(session)

        else:
            logger.error(
                "Unknown payment type: %s",
                payment_type,
            )
            return HttpResponse(status=400)

    except Exception:
        logger.exception(
            "Stripe webhook processing failure."
        )
        return HttpResponse(status=500)

    if not success:
        logger.error(
            "Stripe payment reconciliation required: %s",
            session.get("id"),
        )
        return HttpResponse(status=409)

    return HttpResponse(status=200)
