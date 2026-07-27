from django.contrib import admin
from django.utils.html import format_html

from .models import Allergen, Dish, MenuCategory


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "display_order",
        "name",
        "is_active",
    )

    list_display_links = ("name",)

    list_editable = (
        "display_order",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "display_order",
        "name",
    )

    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
    )

    # prepopulated_fields = {
    #     "slug": ("name",),
    # }


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = (
        "display_order",
        "name",
        "is_active",
    )

    list_display_links = (
        "name",
    )

    list_editable = (
        "display_order",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "display_order",
        "name",
    )


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):

    list_display = (
        "image_preview",
        "name",
        "category",
        "price",
        "is_available",
        "is_delivery_available",
        "is_today_special",
        "is_featured",
    )

    list_display_links = (
        "image_preview",
        "name",
    )

    list_editable = (
        "is_available",
        "is_delivery_available",
        "is_today_special",
        "is_featured",
    )

    list_filter = (
        "category",
        "is_available",
        "is_delivery_available",
        "is_today_special",
        "is_featured",
    )

    search_fields = (
        "name",
        "short_description",
        "description",
    )

    ordering = (
        "category",
        "display_order",
        "name",
    )

    filter_horizontal = (
        "allergens",
    )

    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
        "image_preview",
    )

    autocomplete_fields = (
        "category",
    )

    # prepopulated_fields = {
    #     "slug": ("name",),
    # }

    fieldsets = (

        ("Dish information", {
            "fields": (
                "category",
                "name",
                "slug",
                "short_description",
                "description",
                "price",
                "image",
                "image_preview",
            )
        }),

        ("Availability", {
            "fields": (
                "is_available",
                "is_delivery_available",
                "is_featured",
                "is_today_special",
                "display_order",
            )
        }),

        ("Allergens", {
            "fields": (
                "allergens",
            )
        }),

        ("Dates", {
            "classes": ("collapse",),
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Photo")
    def image_preview(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="70" style="border-radius:8px;" />',
                obj.image.url
            )

        return "—"
