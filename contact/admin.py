from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "subject",
        "email",
        "phone",
        "is_read",
        "created_at",
    )

    list_display_links = (
        "name",
        "subject",
    )

    list_editable = (
        "is_read",
    )

    list_filter = (
        "is_read",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "phone",
        "subject",
        "message",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "name",
        "email",
        "phone",
        "subject",
        "message",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Expéditeur",
            {
                "fields": (
                    "name",
                    "email",
                    "phone",
                )
            },
        ),
        (
            "Message",
            {
                "fields": (
                    "subject",
                    "message",
                )
            },
        ),
        (
            "Traitement",
            {
                "fields": (
                    "is_read",
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

    actions = (
        "mark_as_read",
        "mark_as_unread",
    )

    @admin.action(description="Marquer les messages sélectionnés comme lus")
    def mark_as_read(self, request, queryset):
        updated_count = queryset.update(is_read=True)

        self.message_user(
            request,
            f"{updated_count} message(s) marqué(s) comme lu(s).",
        )

    @admin.action(description="Marquer les messages sélectionnés comme non lus")
    def mark_as_unread(self, request, queryset):
        updated_count = queryset.update(is_read=False)

        self.message_user(
            request,
            f"{updated_count} message(s) marqué(s) comme non lu(s).",
        )