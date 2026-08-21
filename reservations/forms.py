from datetime import date

from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import Reservation


class ReservationForm(forms.ModelForm):
    phone = PhoneNumberField(
        region="FR",
        label="Téléphone",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "tel",
                "placeholder": "06 00 00 00 00",
            }
        ),
    )

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
                    "autocomplete": "given-name",
                    "placeholder": "Votre prénom",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "family-name",
                    "placeholder": "Votre nom",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "email",
                    "placeholder": "vous@email.com",
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
                        "Anniversaire, allergie, chaise bébé, "
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

        return reservation_date