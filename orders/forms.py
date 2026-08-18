from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import DeliveryZone, Order


class CartAddDishForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        label="Quantité",
    )


class CheckoutForm(forms.ModelForm):
    phone = PhoneNumberField(
        region="FR",
        label="Téléphone",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "tel",
            }
        ),
    )

    class Meta:
        model = Order

        fields = (
            "customer_name",
            "email",
            "phone",
            "order_type",
            "address",
            "address_complement",
            "postal_code",
            "city",
            "customer_note",
        )

        widgets = {
            "customer_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "email",
                }
            ),
            "order_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "street-address",
                }
            ),
            "address_complement": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "postal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "postal-code",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "address-level2",
                }
            ),
            "customer_note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "payment_method": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, cart=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.cart = cart
        self.delivery_zone = None
        self.delivery_fee = 0

        # self.fields["payment_method"].choices = [
        #     (
        #         Order.PaymentMethod.CASH,
        #         Order.PaymentMethod.CASH.label,
        #     ),
        # ]

    def clean(self):
        cleaned_data = super().clean()

        order_type = cleaned_data.get("order_type")

        if order_type == Order.OrderType.PICKUP:
            return cleaned_data

        address = cleaned_data.get("address")
        postal_code = cleaned_data.get("postal_code")
        city = cleaned_data.get("city")

        if not address:
            self.add_error(
                "address",
                "Veuillez renseigner l’adresse de livraison.",
            )

        if not postal_code:
            self.add_error(
                "postal_code",
                "Veuillez renseigner le code postal.",
            )

        if not city:
            self.add_error(
                "city",
                "Veuillez renseigner la ville.",
            )

        if not postal_code or not city:
            return cleaned_data

        delivery_zone = (
            DeliveryZone.objects
            .filter(
                postal_code__iexact=postal_code.strip(),
                city__iexact=city.strip(),
                is_active=True,
            )
            .first()
        )

        if delivery_zone is None:
            raise forms.ValidationError(
                "Nous ne livrons pas encore à cette adresse."
            )

        if self.cart is not None:
            subtotal = self.cart.subtotal

            if subtotal < delivery_zone.minimum_order:
                raise forms.ValidationError(
                    (
                        "Le montant minimum de commande pour "
                        f"{delivery_zone.city} est de "
                        f"{delivery_zone.minimum_order:.2f} €."
                    )
                )

            if (
                delivery_zone.free_delivery_from
                and subtotal >= delivery_zone.free_delivery_from
            ):
                self.delivery_fee = 0
            else:
                self.delivery_fee = delivery_zone.delivery_fee

        self.delivery_zone = delivery_zone

        return cleaned_data