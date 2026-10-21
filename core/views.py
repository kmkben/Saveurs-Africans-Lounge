
from django.shortcuts import render

from menu.selectors import get_active_novelties


def home(request):
    novelties = get_active_novelties()[:6]

    return render(
        request,
        "home/index.html",
        {
            "novelties": novelties,
        },
    )
