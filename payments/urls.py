from django.urls import path

from . import views


app_name = "payments"


urlpatterns = [
    # Orders
    path(
        "commande/<int:pk>/",
        views.order_payment,
        name="order",
    ),

    path(
        "commande/<int:pk>/succes/",
        views.order_success,
        name="order_success",
    ),

    path(
        "commande/<int:pk>/annule/",
        views.order_cancel,
        name="order_cancel",
    ),

    # Reservations
    path(
        "reservation/<int:pk>/",
        views.reservation_payment,
        name="reservation",
    ),

    path(
        "reservation/<int:pk>/succes/",
        views.reservation_success,
        name="reservation_success",
    ),

    path(
        "reservation/<int:pk>/annule/",
        views.reservation_cancel,
        name="reservation_cancel",
    ),

    # Stripe webhook
    path(
        "stripe/webhook/",
        views.stripe_webhook,
        name="stripe_webhook",
    ),
]