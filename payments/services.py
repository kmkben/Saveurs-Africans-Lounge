from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

CURRENCY = "eur"


def stripe_to_dict(resource):
    if isinstance(resource, dict):
        return resource
    return resource.to_dict()


def get_stripe_client():
    if not settings.STRIPE_SECRET_KEY:
        raise ImproperlyConfigured("STRIPE_SECRET_KEY is not configured.")
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY)


def euros_to_cents(amount):
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid payment amount.")
    if not value.is_finite() or value <= 0:
        raise ValueError("Payment amount must be positive and finite.")
    cents = int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if cents < 1 or cents > 99999999:
        raise ValueError("Payment amount is outside the supported range.")
    return cents


def retrieve_checkout_session(session_id):
    return stripe_to_dict(get_stripe_client().v1.checkout.sessions.retrieve(session_id))


def expire_checkout_session(session_id):
    return stripe_to_dict(get_stripe_client().v1.checkout.sessions.expire(session_id))


def _create_checkout_session(request, *, email, name, amount, metadata,
                             success_route, cancel_route, pk):
    success_url = request.build_absolute_uri(reverse(success_route, args=[pk]))
    cancel_url = request.build_absolute_uri(reverse(cancel_route, args=[pk]))
    return stripe_to_dict(get_stripe_client().v1.checkout.sessions.create({
        "mode": "payment",
        "payment_method_types": ["card"],
        "customer_email": email,
        "line_items": [{"price_data": {
            "currency": CURRENCY,
            "product_data": {"name": name},
            "unit_amount": euros_to_cents(amount),
        }, "quantity": 1}],
        "metadata": metadata,
        "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
    }))


def create_order_checkout_session(request, order):
    return _create_checkout_session(
        request, email=order.email, name=f"Commande #{order.pk}",
        amount=order.total,
        metadata={"payment_type": "order", "order_id": str(order.pk)},
        success_route="payments:order_success", cancel_route="payments:order_cancel",
        pk=order.pk,
    )


def create_reservation_checkout_session(request, reservation):
    return _create_checkout_session(
        request, email=reservation.email, name="Acompte de réservation",
        amount=reservation.deposit_amount,
        metadata={"payment_type": "reservation", "reservation_id": str(reservation.pk)},
        success_route="payments:reservation_success", cancel_route="payments:reservation_cancel",
        pk=reservation.pk,
    )
