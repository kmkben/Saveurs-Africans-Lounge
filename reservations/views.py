from decimal import Decimal

from django.shortcuts import redirect
from django.views.generic import (
    CreateView,
    DetailView,
    TemplateView,
)

from core.models import SiteSettings

from .forms import ReservationForm
from .models import Reservation


class ReservationCreateView(CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = (
        "reservations/reservation_form.html"
    )

    def form_valid(self, form):
        reservation = form.save(commit=False)

        site_settings = SiteSettings.objects.first()

        if site_settings:
            deposit_amount = (
                site_settings.reservation_deposit_amount
            )
        else:
            deposit_amount = Decimal("15.00")

        reservation.configure_deposit(
            amount=deposit_amount,
        )

        reservation.save()

        self.object = reservation

        self.request.session[
            "last_reservation_id"
        ] = reservation.pk

        return redirect(
            "reservations:deposit",
            pk=reservation.pk,
        )


class ReservationDepositView(DetailView):
    model = Reservation
    template_name = (
        "reservations/reservation_deposit.html"
    )
    context_object_name = "reservation"

    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        reservation = self.get_object()

        if (
            request.session.get(
                "last_reservation_id"
            )
            != reservation.pk
        ):
            return redirect(
                "reservations:create"
            )

        if reservation.deposit_is_paid:
            return redirect(
                "reservations:success"
            )

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )


class ReservationSuccessView(TemplateView):
    template_name = (
        "reservations/reservation_success.html"
    )

    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        reservation_id = request.session.get(
            "last_reservation_id"
        )

        if not reservation_id:
            return redirect(
                "reservations:create"
            )

        reservation = (
            Reservation.objects
            .filter(pk=reservation_id)
            .first()
        )

        if not reservation:
            return redirect(
                "reservations:create"
            )

        if not reservation.deposit_is_paid:
            return redirect(
                "reservations:deposit",
                pk=reservation.pk,
            )

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )

    def get_context_data(
        self,
        **kwargs,
    ):
        context = super().get_context_data(
            **kwargs
        )

        reservation_id = self.request.session.get(
            "last_reservation_id"
        )

        context["reservation"] = (
            Reservation.objects
            .filter(pk=reservation_id)
            .first()
        )

        return context