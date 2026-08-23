from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "reservation_date",
        "reservation_time",
        "full_name",
        "reservation_type",
        "event_type",
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
        "reservation_type",
        "event_type",
        "status",
        "deposit_status",
        "reservation_date",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "event_detail",
        "special_request",
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
                    "reservation_type",
                    "reservation_date",
                    "reservation_time",
                    "end_time",
                    "number_of_guests",
                    "status",
                ),
            },
        ),
        (
            "Événement",
            {
                "fields": (
                    "event_type",
                    "event_detail",
                    "special_request",
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