from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "reservation_date",
        "reservation_time",
        "full_name",
        "number_of_guests",
        "status",
        "deposit_amount",
        "deposit_status",
    )

    list_display_links = (
        "reservation_date",
        "full_name",
    )

    list_editable = (
        "status",
        "deposit_status",
    )

    list_filter = (
        "status",
        "deposit_status",
        "reservation_date",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "deposit_reference",
    )

    ordering = (
        "reservation_date",
        "reservation_time",
    )

    readonly_fields = (
        "deposit_amount",
        "deposit_reference",
        "deposit_paid_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Client",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                ),
            },
        ),
        (
            "Réservation",
            {
                "fields": (
                    "reservation_date",
                    "reservation_time",
                    "number_of_guests",
                    "special_request",
                    "status",
                ),
            },
        ),
        (
            "Acompte",
            {
                "fields": (
                    "deposit_amount",
                    "deposit_status",
                    "deposit_reference",
                    "deposit_paid_at",
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