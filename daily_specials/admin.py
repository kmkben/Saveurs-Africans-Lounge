from django.contrib import admin
from django.utils.html import format_html

from .models import DailySpecial


@admin.register(DailySpecial)
class DailySpecialAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "dish",
        "display_price",
        "image_preview",
        "published",
        "created_at",
    )

    list_display_links = (
        "date",
        "dish",
    )

    list_editable = (
        "published",
    )

    list_filter = (
        "published",
        "date",
    )

    search_fields = (
        "dish__name",
        "note",
    )

    ordering = (
        "-date",
    )

    readonly_fields = (
        "image_preview_large",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Plat du jour",
            {
                "fields": (
                    "dish",
                    "date",
                    "special_price",
                    "note",
                    "published",
                ),
            },
        ),
        (
            "Image de l’offre",
            {
                "fields": (
                    "image",
                    "image_preview_large",
                ),
                "description": (
                    "Vous pouvez ajouter une image spécifique à "
                    "l’offre du jour (plat, boisson, dessert, etc.). "
                    "Sinon, l’image du plat sera utilisée."
                ),
            },
        ),
        (
            "Informations système",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(
        description="Prix affiché",
        ordering="special_price",
    )
    def display_price(self, obj):
        return f"{obj.price:.2f} €"

    @admin.display(description="Image")
    def image_preview(self, obj):
        image = obj.display_image

        if not image:
            return "—"

        return format_html(
            '<img src="{}" '
            'style="width: 60px; height: 60px; '
            'object-fit: cover; border-radius: 8px;">',
            image.url,
        )

    @admin.display(description="Aperçu")
    def image_preview_large(self, obj):
        image = obj.display_image

        if not image:
            return "Aucune image disponible"

        return format_html(
            '<img src="{}" '
            'style="max-width: 320px; max-height: 220px; '
            'object-fit: cover; border-radius: 12px;">',
            image.url,
        )