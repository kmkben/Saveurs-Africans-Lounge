
from django.shortcuts import render

from menu.selectors import get_active_novelties
from promotions.models import Promotion


def home(request):
    novelties = get_active_novelties()[:6]

    promotions = (
        Promotion.objects
        .active()
        .order_by("-starts_on")[:6]
    )

    return render(
        request,
        "home/index.html",
        {
            "novelties": novelties,
            "promotions": promotions,
        },
    )
