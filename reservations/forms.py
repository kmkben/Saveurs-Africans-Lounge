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
            "reservation_type",
            "event_type",
            "event_detail",
            "reservation_date",
            "reservation_time",
            "end_time",
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

            "reservation_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "event_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "event_detail": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Ex. : anniversaire de mariage, "
                        "soirée d’entreprise..."
                    ),
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

            "end_time": forms.TimeInput(
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
                        "Décoration, allergies, chaise bébé, "
                        "configuration particulière..."
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

    def clean(self):
        cleaned_data = super().clean()

        event_type = cleaned_data.get("event_type")
        event_detail = cleaned_data.get("event_detail")

        reservation_time = cleaned_data.get(
            "reservation_time"
        )
        end_time = cleaned_data.get("end_time")

        if (
            event_type == Reservation.EventType.OTHER
            and not event_detail
        ):
            self.add_error(
                "event_detail",
                (
                    "Veuillez préciser le type "
                    "d’événement."
                ),
            )

        if (
            reservation_time
            and end_time
            and end_time <= reservation_time
        ):
            self.add_error(
                "end_time",
                (
                    "L’heure de fin doit être "
                    "postérieure à l’heure de début."
                ),
            )

        return cleaned_data