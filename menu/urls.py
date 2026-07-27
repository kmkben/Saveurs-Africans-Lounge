from django.urls import path

from .views import DishDetailView, MenuListView


app_name = "menu"


urlpatterns = [
    path(
        "",
        MenuListView.as_view(),
        name="list",
    ),
    path(
        "plat/<slug:slug>/",
        DishDetailView.as_view(),
        name="dish_detail",
    ),
]