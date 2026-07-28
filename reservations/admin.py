from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "reservation_date",
        "reservation_time",
        "full_name",
        "number_of_guests",
        "phone",
        "status",
        "requires_deposit",
    )

    list_filter = (
        "status",
        "reservation_date",
        "requires_deposit",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
    )

    ordering = (
        "reservation_date",
        "reservation_time",
    )

    readonly_fields = (
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
                )
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
                )
            },
        ),
        (
            "Acompte",
            {
                "fields": (
                    "requires_deposit",
                    "deposit_amount",
                )
            },
        ),
        (
            "Dates",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )