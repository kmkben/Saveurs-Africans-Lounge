from django.conf import settings

from .models import SiteSettings


def site_settings(request):
    settings_object = SiteSettings.objects.first()

    return {
        "site_settings": settings_object,
        "default_site_name": settings.SITE_NAME,
    }