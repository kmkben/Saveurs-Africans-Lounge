from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import ReservationForm
from .models import Reservation


class ReservationCreateView(CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservations/reservation_form.html"
    success_url = reverse_lazy("reservations:success")


class ReservationSuccessView(TemplateView):
    template_name = "reservations/reservation_success.html"