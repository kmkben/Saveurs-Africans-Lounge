from django import forms

from core.models import SiteSettings
from daily_specials.models import DailySpecial
from events.models import Event
from gallery.models import GalleryAlbum, GalleryImage
from menu.models import Allergen, Dish, MenuCategory
from orders.models import DeliveryZone


# ============================================================
# SHARED FORM STYLING
# ============================================================

class ManagementFormMixin:
    """
    Apply consistent Bootstrap classes to management forms.
    """

    def apply_bootstrap_classes(self):
        for field_name, field in self.fields.items():

            widget = field.widget

            # ------------------------------------------------
            # Checkbox
            # ------------------------------------------------

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault(
                    "class",
                    "form-check-input",
                )

            # ------------------------------------------------
            # Multiple checkboxes
            # ------------------------------------------------

            elif isinstance(
                widget,
                forms.CheckboxSelectMultiple,
            ):
                widget.attrs.setdefault(
                    "class",
                    "management-checkbox-list",
                )

            # ------------------------------------------------
            # File input
            # ------------------------------------------------

            elif isinstance(
                widget,
                forms.ClearableFileInput,
            ):
                widget.attrs.setdefault(
                    "class",
                    "form-control",
                )

            # ------------------------------------------------
            # Select
            # ------------------------------------------------

            elif isinstance(
                widget,
                forms.Select,
            ):
                widget.attrs.setdefault(
                    "class",
                    "form-select",
                )

            # ------------------------------------------------
            # Default input / textarea
            # ------------------------------------------------

            else:
                existing_class = widget.attrs.get(
                    "class",
                    "",
                )

                widget.attrs["class"] = (
                    f"{existing_class} form-control"
                ).strip()


# ============================================================
# DISH
# ============================================================

class DishManagementForm(ManagementFormMixin, forms.ModelForm):

    class Meta:
        model = Dish

        fields = [
            "category",
            "name",
            "short_description",
            "description",
            "price",
            "image",
            "allergens",
            "is_available",
            "is_delivery_available",
            "is_featured",
            "is_today_special",
            "display_order",
            "is_new",
            "new_from",
            "new_until",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Ex. Poulet braisé",
                }
            ),

            "short_description": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Courte description affichée "
                        "sur la carte"
                    ),
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Description détaillée du plat..."
                    ),
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "allergens": forms.CheckboxSelectMultiple(),
            
            "new_from": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),

            "new_until": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),

            "display_order": forms.NumberInput(
                attrs={
                    "min": "0",
                }
            ),
            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()

        self.fields["category"].queryset = (
            MenuCategory.objects.order_by(
                "display_order",
                "name",
            )
        )

        self.fields["allergens"].queryset = (
            Allergen.objects.filter(
                is_active=True,
            ).order_by(
                "display_order",
                "name",
            )
        )
        
        self.fields["new_from"].input_formats = ["%Y-%m-%d"]
        self.fields["new_until"].input_formats = ["%Y-%m-%d"]

    
    
    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("new_from")
        end = cleaned_data.get("new_until")

        if start and end and end < start:
            self.add_error(
                "new_until",
                "La date de fin doit être postérieure à la date de début.",
            )

        return cleaned_data


# ============================================================
# MENU CATEGORY
# ============================================================

class MenuCategoryManagementForm(
    ManagementFormMixin,
    forms.ModelForm,
):

    class Meta:
        model = MenuCategory

        fields = [
            "name",
            "description",
            "display_order",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex. Entrées, Plats, Desserts..."
                    ),
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Description facultative "
                        "de la catégorie"
                    ),
                }
            ),

            "display_order": forms.NumberInput(
                attrs={
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()


# ============================================================
# ALLERGEN
# ============================================================

class AllergenManagementForm(
    ManagementFormMixin,
    forms.ModelForm,
):

    class Meta:
        model = Allergen

        fields = [
            "name",
            "description",
            "icon",
            "display_order",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex. Gluten, arachides, lait..."
                    ),
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": (
                        "Description facultative"
                    ),
                }
            ),

            "icon": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex. fa-solid fa-wheat-awn"
                    ),
                }
            ),

            "display_order": forms.NumberInput(
                attrs={
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()


# ============================================================
# DAILY SPECIAL
# ============================================================

class DailySpecialManagementForm(
    ManagementFormMixin,
    forms.ModelForm,
):

    class Meta:
        model = DailySpecial

        fields = [
            "dish",
            "date",
            "special_price",
            "note",
            "image",
            "published",
        ]

        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),

            "special_price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": (
                        "Laisser vide pour utiliser "
                        "le prix normal"
                    ),
                }
            ),

            "note": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex. Servi avec riz parfumé "
                        "et bissap"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()

        self.fields["dish"].queryset = (
            Dish.objects
            .select_related("category")
            .order_by(
                "category__display_order",
                "display_order",
                "name",
            )
        )

        self.fields["date"].input_formats = [
            "%Y-%m-%d",
        ]


# ============================================================
# DELIVERY ZONE
# ============================================================

class DeliveryZoneManagementForm(
    ManagementFormMixin,
    forms.ModelForm,
):

    class Meta:
        model = DeliveryZone

        fields = [
            "name",
            "postal_code",
            "city",
            "delivery_fee",
            "minimum_order",
            "free_delivery_from",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex. Voiron centre"
                    ),
                }
            ),

            "postal_code": forms.TextInput(
                attrs={
                    "placeholder": "38500",
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "placeholder": "Voiron",
                }
            ),

            "delivery_fee": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "minimum_order": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "free_delivery_from": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": (
                        "Laisser vide si non applicable"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()


# ============================================================
# EVENT
# ============================================================

class EventManagementForm(
    ManagementFormMixin,
    forms.ModelForm,
):

    class Meta:
        model = Event

        fields = [
            "title",
            "short_description",
            "description",
            "image",
            "start_at",
            "end_at",
            "location",
            "price",
            "reservation_required",
            "is_featured",
            "is_published",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex. Soirée afro lounge"
                    ),
                }
            ),

            "short_description": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Résumé de l’événement"
                    ),
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": (
                        "Description complète "
                        "de l’événement..."
                    ),
                }
            ),

            "start_at": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),

            "end_at": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),

            "location": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex. Saveurs Africans Lounge"
                    ),
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": (
                        "Laisser vide si gratuit"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()

        self.fields["start_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        self.fields["end_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

    def clean(self):
        cleaned_data = super().clean()

        start_at = cleaned_data.get(
            "start_at"
        )

        end_at = cleaned_data.get(
            "end_at"
        )

        if (
            start_at
            and end_at
            and end_at <= start_at
        ):
            self.add_error(
                "end_at",
                (
                    "La date de fin doit être "
                    "postérieure à la date de début."
                ),
            )

        return cleaned_data


# ============================================================
# GALLERY ALBUM
# ============================================================

class GalleryAlbumManagementForm(
    ManagementFormMixin,
    forms.ModelForm,
):

    class Meta:
        model = GalleryAlbum

        fields = [
            "title",
            "description",
            "cover_image",
            "category",
            "is_featured",
            "is_published",
            "display_order",
        ]

        labels = {
            "title": "Titre",
            "cover_image": "Image de couverture",
            "category": "Catégorie",
            "is_featured": "Mis en avant",
            "is_published": "Publié",
            "display_order": "Ordre d’affichage",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex. Soirée du 15 août"
                    ),
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Description de l’album..."
                    ),
                }
            ),

            "display_order": forms.NumberInput(
                attrs={
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()


# ============================================================
# GALLERY IMAGE
# ============================================================

class GalleryImageManagementForm(
    ManagementFormMixin,
    forms.ModelForm,
):

    class Meta:
        model = GalleryImage

        # Album is intentionally excluded.
        # The view assigns it from the URL.
        fields = [
            "title",
            "image",
            "caption",
            "is_published",
            "display_order",
        ]

        labels = {
            "title": "Titre",
            "image": "Image",
            "caption": "Légende",
            "is_published": "Publiée",
            "display_order": "Ordre d’affichage",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Titre facultatif"
                    ),
                }
            ),

            "caption": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": (
                        "Légende facultative"
                    ),
                }
            ),

            "display_order": forms.NumberInput(
                attrs={
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()


# ============================================================
# SITE SETTINGS
# ============================================================

class SiteSettingsManagementForm(
    ManagementFormMixin,
    forms.ModelForm,
):

    class Meta:
        model = SiteSettings

        fields = [
            "restaurant_name",
            "tagline",
            "phone",
            "email",
            "address",
            "postal_code",
            "city",
            "google_maps_url",
            "facebook_url",
            "instagram_url",
            "tiktok_url",
            "opening_hours",
            "reservation_deposit_amount",
        ]

        widgets = {
            "restaurant_name": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Saveurs Africans Lounge"
                    ),
                }
            ),

            "tagline": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Slogan du restaurant"
                    ),
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": (
                        "+33 6 00 00 00 00"
                    ),
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": (
                        "contact@example.com"
                    ),
                }
            ),

            "address": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Adresse du restaurant"
                    ),
                }
            ),

            "postal_code": forms.TextInput(
                attrs={
                    "placeholder": "38500",
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "placeholder": "Voiron",
                }
            ),

            "google_maps_url": forms.URLInput(
                attrs={
                    "placeholder": (
                        "https://..."
                    ),
                }
            ),

            "facebook_url": forms.URLInput(
                attrs={
                    "placeholder": (
                        "https://facebook.com/..."
                    ),
                }
            ),

            "instagram_url": forms.URLInput(
                attrs={
                    "placeholder": (
                        "https://instagram.com/..."
                    ),
                }
            ),

            "tiktok_url": forms.URLInput(
                attrs={
                    "placeholder": (
                        "https://tiktok.com/@..."
                    ),
                }
            ),

            "opening_hours": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": (
                        "Ex.\n"
                        "Lundi : fermé\n"
                        "Mardi - Dimanche : "
                        "12h00 - 14h30 / 19h00 - 23h00"
                    ),
                }
            ),

            "reservation_deposit_amount": (
                forms.NumberInput(
                    attrs={
                        "step": "0.01",
                        "min": "0.01",
                    }
                )
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.apply_bootstrap_classes()