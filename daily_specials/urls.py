from django.urls import path

from .views import DailySpecialView


app_name = "daily_specials"


urlpatterns = [
    path(
        "",
        DailySpecialView.as_view(),
        name="home",
    ),
]