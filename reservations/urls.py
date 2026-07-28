from django.urls import path

from .views import ReservationCreateView, ReservationSuccessView


app_name = "reservations"


urlpatterns = [
    path(
        "",
        ReservationCreateView.as_view(),
        name="create",
    ),
    path(
        "confirmation/",
        ReservationSuccessView.as_view(),
        name="success",
    ),
]