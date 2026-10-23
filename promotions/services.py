
from decimal import Decimal

from .models import Promotion


class InvalidPromotionGift(ValueError):
    pass


def get_eligible_promotions(cart):
    """
    Return eligible campaigns and available gifts.
    The first campaign is the default promotion.
    """
    items = list(cart)

    valid_items = [
        item for item in items
        if item["quantity"] > 0
        and item["dish"].is_available
        and item["dish"].category.is_active
    ]

    if not valid_items:
        return []

    subtotal = sum(
        (
            item["price"] * item["quantity"]
            for item in valid_items
        ),
        Decimal("0.00"),
    )

    dish_ids = {
        item["dish"].pk
        for item in valid_items
    }

    campaigns = (
        Promotion.objects
        .active()
        .prefetch_related(
            "eligible_dishes",
            "gift_dishes__category",
        )
        .order_by("-starts_on", "-pk")
    )

    eligible = []

    for promotion in campaigns:
        if subtotal < promotion.minimum_subtotal:
            continue

        restricted_ids = {
            dish.pk
            for dish in promotion.eligible_dishes.all()
        }

        if restricted_ids and not (
            restricted_ids & dish_ids
        ):
            continue

        gifts = [
            dish for dish in promotion.gift_dishes.all()
            if dish.is_available
            and dish.category.is_active
        ]

        if gifts:
            eligible.append({
                "promotion": promotion,
                "gifts": gifts,
            })

    return eligible


def get_selected_gift(cart, promotion_id, gift_id):
    """
    Validate a gift against current active promotions.
    Never trust the posted gift or promotion IDs.
    """
    if not promotion_id or not gift_id:
        raise InvalidPromotionGift(
            "Veuillez sélectionner un cadeau."
        )

    for offer in get_eligible_promotions(cart):
        promotion = offer["promotion"]

        if str(promotion.pk) != str(promotion_id):
            continue

        for gift in offer["gifts"]:
            if str(gift.pk) == str(gift_id):
                return promotion, gift

    raise InvalidPromotionGift(
        "Ce cadeau promotionnel n'est plus disponible."
    )
