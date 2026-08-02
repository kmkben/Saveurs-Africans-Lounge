from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Restaurant",
            {
                "fields": (
                    "restaurant_name",
                    "tagline",
                )
            },
        ),
        (
            "Coordonnées",
            {
                "fields": (
                    "phone",
                    "email",
                    "address",
                    "postal_code",
                    "city",
                    "google_maps_url",
                )
            },
        ),
        (
            "Réseaux sociaux",
            {
                "fields": (
                    "facebook_url",
                    "instagram_url",
                    "tiktok_url",
                )
            },
        ),
        (
            "Horaires",
            {
                "fields": (
                    "opening_hours",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False