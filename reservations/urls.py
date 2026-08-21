from django.urls import path

from .views import (
    ReservationCreateView,
    ReservationDepositView,
    ReservationSuccessView,
)


app_name = "reservations"


urlpatterns = [
    path(
        "",
        ReservationCreateView.as_view(),
        name="create",
    ),

    path(
        "<int:pk>/acompte/",
        ReservationDepositView.as_view(),
        name="deposit",
    ),

    path(
        "confirmation/",
        ReservationSuccessView.as_view(),
        name="success",
    ),
]