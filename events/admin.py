from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_at",
        "location",
        "is_featured",
        "is_published",
    )

    list_display_links = (
        "title",
    )

    list_editable = (
        "is_featured",
        "is_published",
    )

    list_filter = (
        "is_published",
        "is_featured",
        "reservation_required",
        "start_at",
    )

    search_fields = (
        "title",
        "short_description",
        "description",
        "location",
    )

    ordering = (
        "start_at",
    )

    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Informations principales",
            {
                "fields": (
                    "title",
                    "slug",
                    "short_description",
                    "description",
                    "image",
                )
            },
        ),
        (
            "Date et lieu",
            {
                "fields": (
                    "start_at",
                    "end_at",
                    "location",
                )
            },
        ),
        (
            "Tarif et réservation",
            {
                "fields": (
                    "price",
                    "reservation_required",
                )
            },
        ),
        (
            "Publication",
            {
                "fields": (
                    "is_featured",
                    "is_published",
                )
            },
        ),
        (
            "Dates techniques",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )