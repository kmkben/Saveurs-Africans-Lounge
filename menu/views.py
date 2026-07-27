from django.shortcuts import render
from django.db.models import Prefetch
from django.views.generic import DetailView, ListView

from .models import Allergen, Dish, MenuCategory

# Create your views here.


class MenuListView(ListView):
    """
    Displays all active menu categories and their available dishes.
    """

    model = MenuCategory
    template_name = "menu/menu_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        active_allergens = Allergen.objects.filter(
            is_active=True,
        ).order_by(
            "display_order",
            "name",
        )

        available_dishes = (
            Dish.objects
            .filter(is_available=True)
            .prefetch_related(
                Prefetch(
                    "allergens",
                    queryset=active_allergens,
                )
            )
            .order_by(
                "display_order",
                "name",
            )
        )

        return (
            MenuCategory.objects
            .filter(is_active=True)
            .prefetch_related(
                Prefetch(
                    "dishes",
                    queryset=available_dishes,
                    to_attr="available_dishes",
                )
            )
            .order_by(
                "display_order",
                "name",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["today_specials"] = (
            Dish.objects
            .filter(
                is_available=True,
                is_today_special=True,
                category__is_active=True,
            )
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "allergens",
                    queryset=Allergen.objects.filter(is_active=True),
                )
            )
            .order_by(
                "display_order",
                "name",
            )
        )

        context["featured_dishes"] = (
            Dish.objects
            .filter(
                is_available=True,
                is_featured=True,
                category__is_active=True,
            )
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "allergens",
                    queryset=Allergen.objects.filter(is_active=True),
                )
            )
            .order_by(
                "display_order",
                "name",
            )
        )

        return context


class DishDetailView(DetailView):
    """
    Displays the details of one available dish.
    """

    model = Dish
    template_name = "menu/dish_detail.html"
    context_object_name = "dish"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Dish.objects
            .filter(
                is_available=True,
                category__is_active=True,
            )
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "allergens",
                    queryset=Allergen.objects.filter(
                        is_active=True,
                    ).order_by(
                        "display_order",
                        "name",
                    ),
                )
            )
        )
