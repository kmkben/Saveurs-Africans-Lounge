
from django.contrib import admin

from .models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "starts_on",
        "ends_on",
        "minimum_subtotal",
        "is_active",
    )

    list_filter = (
        "is_active",
        "starts_on",
        "ends_on",
    )

    search_fields = (
        "title",
        "description",
    )

    filter_horizontal = (
        "eligible_dishes",
        "gift_dishes",
    )
