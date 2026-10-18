from django.db.models import Q
from django.utils import timezone

from .models import Dish


def get_active_novelties():
    today = timezone.localdate()

    return (
        Dish.objects
        .select_related("category")
        .filter(
            is_new=True,
            is_available=True,
            category__is_active=True,
        )
        .filter(
            Q(new_from__isnull=True) |
            Q(new_from__lte=today)
        )
        .filter(
            Q(new_until__isnull=True) |
            Q(new_until__gte=today)
        )
        .order_by("-created_at")
    )