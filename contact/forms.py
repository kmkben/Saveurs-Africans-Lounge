from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    phone = PhoneNumberField(
        required=False,
        region="FR",
        label="Téléphone",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "06 00 00 00 00",
                "autocomplete": "tel",
            }
        ),
    )

    class Meta:
        model = ContactMessage

        fields = (
            "name",
            "email",
            "phone",
            "subject",
            "subject_detail",
            "message",
        )

        labels = {
            "name": "Nom complet",
            "email": "Adresse e-mail",
            "subject": "Sujet",
            "subject_detail": "Précision",
            "message": "Message",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Votre nom complet",
                    "autocomplete": "name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "vous@email.com",
                    "autocomplete": "email",
                }
            ),
            "subject": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "subject_detail": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex. : anniversaire pour 20 personnes",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Écrivez votre message ici...",
                }
            ),
        }