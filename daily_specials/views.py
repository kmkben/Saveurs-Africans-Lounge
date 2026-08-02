from django.utils import timezone
from django.views.generic import TemplateView

from .models import DailySpecial


class DailySpecialView(TemplateView):
    template_name = "daily_specials/daily_special.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()

        daily_special = (
            DailySpecial.objects
            .select_related("dish")
            .filter(
                date=today,
                published=True,
            )
            .first()
        )

        context.update(
            {
                "today": today,
                "daily_special": daily_special,
            }
        )

        return context