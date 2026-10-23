from django.contrib import messages
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from decimal import Decimal
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse

from menu.models import Dish

from .cart import Cart
from .forms import CartAddDishForm, CheckoutForm
from .models import OrderItem, DeliveryZone, Order


from promotions.services import (
    get_eligible_promotions,
    get_selected_gift,
    InvalidPromotionGift,
)



def cart_detail(request):
    cart = Cart(request)

    return render(
        request,
        "orders/cart.html",
        {
            "cart": cart,
        },
    )


@require_POST
def cart_add(request, dish_id):
    cart = Cart(request)

    dish = get_object_or_404(
        Dish,
        pk=dish_id,
    )

    form = CartAddDishForm(request.POST)

    if form.is_valid():
        cart.add(
            dish=dish,
            quantity=form.cleaned_data["quantity"],
        )

        messages.success(
            request,
            f"{dish.name} a été ajouté à votre panier.",
        )

    return redirect("orders:cart")


@require_POST
def cart_update(request, dish_id):
    cart = Cart(request)

    dish = get_object_or_404(
        Dish,
        pk=dish_id,
    )

    form = CartAddDishForm(request.POST)

    if form.is_valid():
        cart.add(
            dish=dish,
            quantity=form.cleaned_data["quantity"],
            override_quantity=True,
        )

    return redirect("orders:cart")


@require_POST
def cart_remove(request, dish_id):
    cart = Cart(request)

    dish = get_object_or_404(
        Dish,
        pk=dish_id,
    )

    cart.remove(dish)

    messages.success(
        request,
        f"{dish.name} a été retiré du panier.",
    )

    return redirect("orders:cart")



@transaction.atomic
def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.info(request, "Votre panier est vide.")
        return redirect("orders:cart")

    # Refresh prices and validate all products before checkout.
    cart_items = list(cart)

    for item in cart_items:
        dish = item["dish"]

        if (
            not dish.is_available
            or not dish.category.is_active
            or (
                not dish.is_delivery_available
                and request.method == "POST"
                and request.POST.get("order_type") == Order.OrderType.DELIVERY
            )
        ):
            messages.error(
                request,
                f"{dish.name} n'est plus disponible pour cette commande.",
            )
            return redirect("orders:cart")

        # Session prices must not determine the actual charge.
        cart.cart[str(dish.pk)]["price"] = str(dish.price)

    if len(cart_items) != len(cart.cart):
        messages.error(
            request,
            "Certains produits du panier ne sont plus disponibles.",
        )
        return redirect("orders:cart")

    cart.save()
    cart_items = list(cart)

    offers = get_eligible_promotions(cart)

    # V1: one active campaign per order.
    selected_offer = offers[0] if offers else None

    if request.method == "POST":
        form = CheckoutForm(request.POST, cart=cart)

        if form.is_valid():
            selected_promotion = None
            selected_gift = None

            if selected_offer:
                try:
                    selected_promotion, selected_gift = get_selected_gift(
                        cart=cart,
                        promotion_id=request.POST.get("promotion_id"),
                        gift_id=request.POST.get("gift_id"),
                    )

                    if selected_promotion.pk != selected_offer["promotion"].pk:
                        raise InvalidPromotionGift(
                            "Cette promotion n'est plus disponible."
                        )

                except InvalidPromotionGift as exc:
                    form.add_error(None, str(exc))

            if not form.errors:
                order = form.save(commit=False)

                order.payment_method = Order.PaymentMethod.ONLINE
                order.payment_status = Order.PaymentStatus.PENDING

                if order.order_type == Order.OrderType.PICKUP:
                    order.address = ""
                    order.address_complement = ""
                    order.postal_code = ""
                    order.city = ""
                    order.delivery_zone = None
                    order.delivery_fee = Decimal("0.00")
                else:
                    order.delivery_zone = form.delivery_zone
                    order.delivery_fee = form.delivery_fee

                # Revalidate delivery availability using cleaned form data.
                if (
                    order.order_type == Order.OrderType.DELIVERY
                    and any(
                        not item["dish"].is_delivery_available
                        for item in cart_items
                    )
                ):
                    form.add_error(
                        None,
                        "Un produit du panier n'est pas livrable.",
                    )
                else:
                    order.save()

                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            dish=item["dish"],
                            dish_name=item["dish"].name,
                            unit_price=item["price"],
                            quantity=item["quantity"],
                        )

                    if selected_gift:
                        OrderItem.objects.create(
                            order=order,
                            dish=selected_gift,
                            dish_name=selected_gift.name,
                            unit_price=Decimal("0.00"),
                            quantity=1,
                            is_promotional_gift=True,
                            promotion=selected_promotion,
                            promotion_name=selected_promotion.title,
                        )

                    request.session["pending_order_id"] = order.pk

                    return redirect(
                        "orders:payment",
                        order_id=order.pk,
                    )

    else:
        form = CheckoutForm(cart=cart)

    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "form": form,
            "selected_offer": selected_offer,
        },
    )



def order_success(request, order_id):
    order = get_object_or_404(
        Order,
        pk=order_id,
    )
    
    if request.session.get("last_order_id") != order.pk:
        return redirect("orders:cart")

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
        },
    )
    
    
    
    
@require_GET
def delivery_quote(request):
    postal_code = request.GET.get("postal_code", "").strip()
    city = request.GET.get("city", "").strip()

    try:
        subtotal = Cart(request).subtotal
    except Exception:
        subtotal = 0

    if not postal_code or not city:
        return JsonResponse(
            {
                "success": False,
                "message": "Veuillez renseigner le code postal et la ville.",
            },
            status=400,
        )

    zone = (
        DeliveryZone.objects
        .filter(
            postal_code__iexact=postal_code,
            city__iexact=city,
            is_active=True,
        )
        .first()
    )

    if zone is None:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Cette adresse ne fait pas partie "
                    "de nos zones de livraison."
                ),
            },
            status=404,
        )

    if subtotal < zone.minimum_order:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    f"Commande minimum pour {zone.city} : "
                    f"{zone.minimum_order:.2f} €."
                ),
            },
            status=400,
        )

    delivery_fee = zone.delivery_fee

    if (
        zone.free_delivery_from
        and subtotal >= zone.free_delivery_from
    ):
        delivery_fee = 0

    total = subtotal + delivery_fee

    return JsonResponse(
        {
            "success": True,
            "zone": zone.name,
            "delivery_fee": f"{delivery_fee:.2f}",
            "subtotal": f"{subtotal:.2f}",
            "total": f"{total:.2f}",
        }
    )
    
    
    
#from django.shortcuts import get_object_or_404


def order_payment_page(request, order_id):
    order = get_object_or_404(
        Order,
        pk=order_id,
    )

    if request.session.get("pending_order_id") != order.pk:
        return redirect("orders:cart")

    if order.payment_status == Order.PaymentStatus.PAID:
        return redirect(
            "orders:success",
            order_id=order.pk,
        )

    return render(
        request,
        "orders/payment.html",
        {
            "order": order,
        },
    )