import stripe

from django.conf import settings
from django.urls import reverse


stripe.api_key = settings.STRIPE_SECRET_KEY


def create_order_checkout_session(request, order):
    success_url = request.build_absolute_uri(
        reverse("payments:order_success", args=[order.pk])
    )

    cancel_url = request.build_absolute_uri(
        reverse("payments:order_cancel", args=[order.pk])
    )

    session = stripe.checkout.Session.create(
        mode="payment",

        customer_email=order.email,

        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"Commande #{order.pk}",
                    },
                    "unit_amount": int(order.total * 100),
                },
                "quantity": 1,
            }
        ],

        metadata={
            "payment_type": "order",
            "order_id": str(order.pk),
        },

        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
    )

    return session


def create_reservation_checkout_session(request, reservation):
    success_url = request.build_absolute_uri(
        reverse(
            "payments:reservation_success",
            args=[reservation.pk],
        )
    )

    cancel_url = request.build_absolute_uri(
        reverse(
            "payments:reservation_cancel",
            args=[reservation.pk],
        )
    )

    session = stripe.checkout.Session.create(
        mode="payment",

        customer_email=reservation.email,

        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "Acompte de réservation",
                    },
                    "unit_amount": int(
                        reservation.deposit_amount * 100
                    ),
                },
                "quantity": 1,
            }
        ],

        metadata={
            "payment_type": "reservation",
            "reservation_id": str(reservation.pk),
        },

        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
    )

    return session