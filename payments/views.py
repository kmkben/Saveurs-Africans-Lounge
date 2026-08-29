import stripe

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.cart import Cart
from orders.models import Order
from reservations.models import Reservation

from .services import (
    create_order_checkout_session,
    create_reservation_checkout_session,
)

from notifications.services import (
    send_order_paid_notifications,
    send_reservation_paid_notifications,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


# ==================================================
# ORDER PAYMENT
# ==================================================

@require_POST
def order_payment(request, pk):
    order = get_object_or_404(
        Order,
        pk=pk,
    )

    if order.payment_status == Order.PaymentStatus.PAID:
        return redirect(
            "orders:success",
            order_id=order.pk,
        )

    session = create_order_checkout_session(
        request,
        order,
    )

    order.payment_reference = session.id
    order.save(
        update_fields=[
            "payment_reference",
        ]
    )

    return redirect(
        session.url,
        code=303,
    )


def order_success(request, pk):
    order = get_object_or_404(
        Order,
        pk=pk,
    )

    session_id = request.GET.get("session_id")

    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(
                session_id
            )

        except stripe.StripeError:
            messages.error(
                request,
                (
                    "Impossible de vérifier le paiement "
                    "pour le moment."
                ),
            )

            return redirect(
                "orders:payment",
                order_id=order.pk,
            )

        metadata = session.metadata

        order_id = metadata["order_id"]

        if (
            session.payment_status == "paid"
            and order_id == str(order.pk)
        ):
            order.payment_status = (
                Order.PaymentStatus.PAID
            )

            order.amount_paid = order.total
            order.payment_reference = session.id
            order.paid_at = timezone.now()

            order.save(
                update_fields=[
                    "payment_status",
                    "amount_paid",
                    "payment_reference",
                    "paid_at",
                ]
            )
            
            send_order_paid_notifications(order)

            Cart(request).clear()

            request.session["last_order_id"] = order.pk
            request.session.pop(
                "pending_order_id",
                None,
            )

    if order.payment_status != Order.PaymentStatus.PAID:
        messages.warning(
            request,
            (
                "Le paiement n’a pas encore été "
                "confirmé."
            ),
        )

        return redirect(
            "orders:payment",
            order_id=order.pk,
        )

    return redirect(
        "orders:success",
        order_id=order.pk,
    )


def order_cancel(request, pk):
    order = get_object_or_404(
        Order,
        pk=pk,
    )

    request.session["pending_order_id"] = order.pk

    messages.warning(
        request,
        (
            "Le paiement a été annulé. "
            "Votre commande reste en attente "
            "de paiement."
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

    if reservation.deposit_is_paid:
        request.session[
            "last_reservation_id"
        ] = reservation.pk

        return redirect(
            "reservations:success",
        )

    session = create_reservation_checkout_session(
        request,
        reservation,
    )

    reservation.deposit_reference = session.id

    reservation.save(
        update_fields=[
            "deposit_reference",
        ]
    )

    return redirect(
        session.url,
        code=303,
    )


def reservation_success(request, pk):
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
    )

    session_id = request.GET.get("session_id")

    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(
                session_id
            )

        except stripe.StripeError:
            messages.error(
                request,
                (
                    "Impossible de vérifier le paiement "
                    "de l’acompte pour le moment."
                ),
            )

            return redirect(
                "reservations:deposit",
                pk=reservation.pk,
            )

        metadata = session.metadata

        reservation_id = metadata[
            "reservation_id"
        ]

        if (
            session.payment_status == "paid"
            and reservation_id == str(reservation.pk)
        ):
            reservation.deposit_status = (
                Reservation.DepositStatus.PAID
            )

            reservation.deposit_reference = session.id
            reservation.deposit_paid_at = timezone.now()

            reservation.save(
                update_fields=[
                    "deposit_status",
                    "deposit_reference",
                    "deposit_paid_at",
                ]
            )
            
            send_reservation_paid_notifications(reservation)

    if not reservation.deposit_is_paid:
        messages.warning(
            request,
            (
                "Le paiement de l’acompte "
                "n’a pas encore été confirmé."
            ),
        )

        return redirect(
            "reservations:deposit",
            pk=reservation.pk,
        )

    request.session[
        "last_reservation_id"
    ] = reservation.pk

    return redirect(
        "reservations:success",
    )


def reservation_cancel(request, pk):
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
    )

    request.session[
        "last_reservation_id"
    ] = reservation.pk

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
    payload = request.body

    signature = request.META.get(
        "HTTP_STRIPE_SIGNATURE",
        "",
    )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)


    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        metadata = session["metadata"]

        payment_type = metadata["payment_type"]

        if session["payment_status"] == "paid":

            if payment_type == "order":
                _mark_order_paid(session)

            elif payment_type == "reservation":
                _mark_reservation_paid(session)


    return HttpResponse(status=200)


# ==================================================
# PAYMENT HELPERS
# ==================================================

def _mark_order_paid(session):
    metadata = session["metadata"]

    order_id = metadata["order_id"]

    if not order_id:
        return

    try:
        order = Order.objects.get(
            pk=order_id,
        )

    except Order.DoesNotExist:
        return


    if order.payment_status == Order.PaymentStatus.PAID:
        return


    order.payment_status = (
        Order.PaymentStatus.PAID
    )

    order.amount_paid = order.total
    order.payment_reference = session["id"]
    order.paid_at = timezone.now()

    order.save(
        update_fields=[
            "payment_status",
            "amount_paid",
            "payment_reference",
            "paid_at",
        ]
    )
    
    send_order_paid_notifications(order)


def _mark_reservation_paid(session):
    metadata = session["metadata"]

    reservation_id = metadata[
        "reservation_id"
    ]

    if not reservation_id:
        return


    try:
        reservation = Reservation.objects.get(
            pk=reservation_id,
        )

    except Reservation.DoesNotExist:
        return


    if reservation.deposit_is_paid:
        return


    reservation.deposit_status = (
        Reservation.DepositStatus.PAID
    )

    reservation.deposit_reference = session["id"]
    reservation.deposit_paid_at = timezone.now()

    reservation.save(
        update_fields=[
            "deposit_status",
            "deposit_reference",
            "deposit_paid_at",
        ]
    )
    
    send_reservation_paid_notifications(reservation)