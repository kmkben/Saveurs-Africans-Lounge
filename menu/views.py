
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.views.generic import DetailView, ListView

from promotions.models import Promotion
from .models import Allergen, Dish, MenuCategory


# ============================================================
# MARKETING HELPERS
# ============================================================

def get_active_novelty_filter():
    """
    Return a filter for currently active novelties.

    A novelty is active when:
    - is_new is True
    - new_from is empty or has already passed
    - new_until is empty or has not yet passed
    """
    today = timezone.localdate()

    return (
        Q(is_new=True)
        & (Q(new_from__isnull=True) | Q(new_from__lte=today))
        & (Q(new_until__isnull=True) | Q(new_until__gte=today))
    )


def get_menu_promotions():
    """
    Return active promotions that have at least one
    available promotional gift.
    """
    promotions = (
        Promotion.objects.active()
        .prefetch_related(
            "eligible_dishes",
            "gift_dishes__category",
        )
        .order_by("-starts_on", "-pk")
    )

    return [
        promotion
        for promotion in promotions
        if any(
            gift.is_available and gift.category.is_active
            for gift in promotion.gift_dishes.all()
        )
    ]


def build_promotion_index(promotions):
    """
    Organize promotions by eligible dish.

    If eligible_dishes is empty, the promotion applies
    to every available product in the menu.
    """
    universal_promotions = []
    promotions_by_dish = {}

    for promotion in promotions:
        eligible_ids = [
            dish.pk for dish in promotion.eligible_dishes.all()
        ]

        if not eligible_ids:
            universal_promotions.append(promotion)
            continue

        for dish_id in eligible_ids:
            promotions_by_dish.setdefault(dish_id, []).append(promotion)

    return universal_promotions, promotions_by_dish


def attach_marketing_info(dishes, novelty_ids, universal_promotions, promotions_by_dish):
    """
    Attach marketing information to Dish instances
    for use in Django templates.
    """
    for dish in dishes:
        dish.is_active_novelty = dish.pk in novelty_ids

        dish.active_promotions = (
            universal_promotions + promotions_by_dish.get(dish.pk, [])
        )

        dish.has_active_promotion = bool(dish.active_promotions)


# ============================================================
# MENU LIST
# ============================================================

class MenuListView(ListView):
    """
    Display all active menu categories and their
    available dishes, including marketing information.
    """

    model = MenuCategory
    template_name = "menu/menu_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        active_allergens = Allergen.objects.filter(
            is_active=True
        ).order_by("display_order", "name")

        available_dishes = (
            Dish.objects
            .filter(is_available=True)
            .prefetch_related(
                Prefetch("allergens", queryset=active_allergens)
            )
            .order_by("display_order", "name")
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
            .order_by("display_order", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_allergens = Allergen.objects.filter(
            is_active=True
        ).order_by("display_order", "name")

        # Today's specials
        context["today_specials"] = list(
            Dish.objects
            .filter(
                is_available=True,
                is_today_special=True,
                category__is_active=True,
            )
            .select_related("category")
            .prefetch_related(
                Prefetch("allergens", queryset=active_allergens)
            )
            .order_by("display_order", "name")
        )

        # Featured products
        context["featured_dishes"] = list(
            Dish.objects
            .filter(
                is_available=True,
                is_featured=True,
                category__is_active=True,
            )
            .select_related("category")
            .prefetch_related(
                Prefetch("allergens", queryset=active_allergens)
            )
            .order_by("display_order", "name")
        )

        # Active promotions
        promotions = get_menu_promotions()

        universal_promotions, promotions_by_dish = build_promotion_index(
            promotions
        )

        # Active novelties
        novelty_ids = set(
            Dish.objects
            .filter(
                get_active_novelty_filter(),
                is_available=True,
                category__is_active=True,
            )
            .values_list("pk", flat=True)
        )

        # Marketing information for category products
        for category in context["categories"]:
            attach_marketing_info(
                category.available_dishes,
                novelty_ids,
                universal_promotions,
                promotions_by_dish,
            )

        # Marketing information for today's specials
        attach_marketing_info(
            context["today_specials"],
            novelty_ids,
            universal_promotions,
            promotions_by_dish,
        )

        # Marketing information for featured products
        attach_marketing_info(
            context["featured_dishes"],
            novelty_ids,
            universal_promotions,
            promotions_by_dish,
        )

        context["active_promotions"] = promotions

        return context


# ============================================================
# DISH DETAIL
# ============================================================

class DishDetailView(DetailView):
    """
    Display one available dish with its allergens,
    active novelty status and applicable promotions.
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
                        is_active=True
                    ).order_by("display_order", "name"),
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dish = self.object

        # Active promotions
        promotions = get_menu_promotions()

        universal_promotions, promotions_by_dish = build_promotion_index(
            promotions
        )

        # Check if this dish is currently a novelty
        novelty_ids = set(
            Dish.objects
            .filter(
                get_active_novelty_filter(),
                pk=dish.pk,
            )
            .values_list("pk", flat=True)
        )

        # Attach marketing information to this dish
        attach_marketing_info(
            [dish],
            novelty_ids,
            universal_promotions,
            promotions_by_dish,
        )

        return context
