from datetime import date

from django import forms

from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "reservation_date",
            "reservation_time",
            "number_of_guests",
            "special_request",
        )

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Votre prénom",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Votre nom",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "vous@exemple.fr",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "06 00 00 00 00",
                }
            ),
            "reservation_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "reservation_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),
            "number_of_guests": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
            "special_request": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Anniversaire, chaise bébé, allergie, "
                        "demande particulière..."
                    ),
                }
            ),
        }

    def clean_reservation_date(self):
        reservation_date = self.cleaned_data["reservation_date"]

        if reservation_date < date.today():
            raise forms.ValidationError(
                "La date de réservation ne peut pas être dans le passé."
            )

        if reservation_date.weekday() in (0, 6):
            raise forms.ValidationError(
                "Le restaurant est fermé le lundi et le dimanche."
            )

        return reservation_date