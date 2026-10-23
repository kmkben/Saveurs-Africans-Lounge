from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db import models
from django.db.models import ProtectedError, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from contact.models import ContactMessage
from core.models import SiteSettings
from daily_specials.models import DailySpecial
from events.models import Event
from gallery.models import GalleryAlbum, GalleryImage
from menu.models import Allergen, Dish, MenuCategory
from orders.models import DeliveryZone, Order
from reservations.models import Reservation

from .forms import (
    AllergenManagementForm,
    DailySpecialManagementForm,
    DeliveryZoneManagementForm,
    DishManagementForm,
    EventManagementForm,
    GalleryAlbumManagementForm,
    GalleryImageManagementForm,
    MenuCategoryManagementForm,
    SiteSettingsManagementForm,
)

from promotions.models import Promotion
from .forms import PromotionManagementForm


# ============================================================
# ACCESS CONTROL
# ============================================================

def staff_required(view_func):
    """
    Restrict the management area to authenticated staff users.
    """

    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url="/gestion/connexion/",
    )(view_func)



# ==========================================================
# MANAGEMENT AUTHENTICATION
# ==========================================================


def management_login(request):
    
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("management:dashboard")

    form = AuthenticationForm(
        request=request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():

        user = form.get_user()

        if not user.is_staff:

            messages.error(
                request,
                "Ce compte n’est pas autorisé à accéder à l’espace de gestion.",
            )

        else:

            login(request, user)

            next_url = request.GET.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect("management:dashboard")

    return render(
        request,
        "management/auth/manage_login.html",
        {
            "form": form,
        },
    )


@require_POST
def management_logout(request):
    """
    End the current management session.
    """

    logout(request)

    return redirect("management:login")



# ============================================================
# DASHBOARD
# ============================================================

@staff_required
def dashboard(request):
    """
    Main restaurant management dashboard.
    """

    today = timezone.localdate()
    now = timezone.now()

    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    today_orders = (
        Order.objects
        .filter(
            created_at__date=today,
            payment_status=Order.PaymentStatus.PAID,
        )
        .prefetch_related("items")
        .order_by("-created_at")
    )

    orders_count = today_orders.count()

    active_orders_count = (
        today_orders
        .exclude(
            status__in=[
                Order.Status.COMPLETED,
                Order.Status.CANCELLED,
            ]
        )
        .count()
    )

    today_revenue = (
        today_orders
        .aggregate(
            total=Sum("amount_paid"),
        )
        .get("total")
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Reservations
    # --------------------------------------------------------

    today_reservations = (
        Reservation.objects
        .filter(
            reservation_date=today,
            deposit_status=Reservation.DepositStatus.PAID,
        )
        .exclude(
            status=Reservation.Status.CANCELLED,
        )
        .order_by("reservation_time")
    )

    reservations_count = today_reservations.count()

    guests_count = (
        today_reservations
        .aggregate(
            total=models.Sum("number_of_guests"),
        )
        .get("total")
        or 0
    )

    upcoming_reservations = (
        Reservation.objects
        .filter(
            reservation_date__gte=today,
            deposit_status=Reservation.DepositStatus.PAID,
        )
        .exclude(
            status__in=[
                Reservation.Status.CANCELLED,
                Reservation.Status.COMPLETED,
            ]
        )
        .order_by(
            "reservation_date",
            "reservation_time",
        )[:8]
    )

    # --------------------------------------------------------
    # Contact messages
    # --------------------------------------------------------

    unread_messages_count = ContactMessage.objects.filter(
        is_read=False,
    ).count()

    recent_messages = (
        ContactMessage.objects
        .filter(is_read=False)
        .order_by("-created_at")[:5]
    )

    # --------------------------------------------------------
    # Daily special
    # --------------------------------------------------------

    today_special = (
        DailySpecial.objects
        .select_related("dish")
        .filter(
            date=today,
            published=True,
        )
        .first()
    )

    # --------------------------------------------------------
    # Upcoming events
    # --------------------------------------------------------

    upcoming_events = (
        Event.objects
        .filter(
            start_at__gte=now,
            is_published=True,
        )
        .order_by("start_at")[:5]
    )

    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    context = {
        "today": today,

        "today_orders": today_orders[:8],
        "orders_count": orders_count,
        "active_orders_count": active_orders_count,
        "today_revenue": today_revenue,

        "today_reservations": today_reservations,
        "reservations_count": reservations_count,
        "guests_count": guests_count,
        "upcoming_reservations": upcoming_reservations,

        "unread_messages_count": unread_messages_count,
        "recent_messages": recent_messages,

        "today_special": today_special,
        "upcoming_events": upcoming_events,
    }

    return render(
        request,
        "management/dashboard.html",
        context,
    )


# ============================================================
# ORDERS
# ============================================================

@staff_required
def orders_list(request):
    """
    Display all orders.
    """

    orders = (
        Order.objects
        .select_related("delivery_zone")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    # --------------------------------------------------------
    # Optional status filter
    # --------------------------------------------------------

    selected_status = request.GET.get("status", "").strip()

    valid_statuses = {
        value
        for value, label in Order.Status.choices
    }

    if selected_status in valid_statuses:
        orders = orders.filter(status=selected_status)

    # --------------------------------------------------------
    # Optional order type filter
    # --------------------------------------------------------

    selected_type = request.GET.get("type", "").strip()

    valid_types = {
        value
        for value, label in Order.OrderType.choices
    }

    if selected_type in valid_types:
        orders = orders.filter(order_type=selected_type)

    context = {
        "orders": orders,
        "status_choices": Order.Status.choices,
        "order_type_choices": Order.OrderType.choices,
        "selected_status": selected_status,
        "selected_type": selected_type,
    }

    return render(
        request,
        "management/orders/manage_orders_list.html",
        context,
    )


@staff_required
def order_detail(request, order_id):
    """
    Display the complete details of an order.
    """

    order = get_object_or_404(
        Order.objects
        .select_related("delivery_zone")
        .prefetch_related(
            "items",
            "items__dish",
        ),
        pk=order_id,
    )

    context = {
        "order": order,
        "status_choices": Order.Status.choices,
    }

    return render(
        request,
        "management/orders/manage_order_detail.html",
        context,
    )


@staff_required
@require_POST
def order_status_update(request, order_id):
    """
    Update the operational status of an order.

    Payment information is intentionally not modified here.
    """

    order = get_object_or_404(
        Order,
        pk=order_id,
    )

    new_status = request.POST.get(
        "status",
        "",
    ).strip()

    valid_statuses = {
        value
        for value, label in Order.Status.choices
    }

    if new_status not in valid_statuses:
        messages.error(
            request,
            "Le statut sélectionné est invalide.",
        )

        return redirect(
            "management:order_detail",
            order_id=order.pk,
        )

    # --------------------------------------------------------
    # Delivery status is not valid for pickup orders
    # --------------------------------------------------------

    if (
        new_status == Order.Status.OUT_FOR_DELIVERY
        and order.order_type != Order.OrderType.DELIVERY
    ):
        messages.error(
            request,
            (
                "Une commande à emporter ne peut pas être "
                "placée en livraison."
            ),
        )

        return redirect(
            "management:order_detail",
            order_id=order.pk,
        )

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    if order.status == new_status:
        messages.info(
            request,
            "La commande possède déjà ce statut.",
        )

        return redirect(
            "management:order_detail",
            order_id=order.pk,
        )

    order.status = new_status

    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            f"Le statut de la commande #{order.pk} "
            "a été mis à jour."
        ),
    )

    return redirect(
        "management:order_detail",
        order_id=order.pk,
    )


# ============================================================
# RESERVATIONS
# ============================================================

@staff_required
def reservations_list(request):
    """
    Display all reservations.
    """

    reservations = Reservation.objects.all()

    # --------------------------------------------------------
    # Optional status filter
    # --------------------------------------------------------

    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    valid_statuses = {
        value
        for value, label in Reservation.Status.choices
    }

    if selected_status in valid_statuses:
        reservations = reservations.filter(
            status=selected_status,
        )

    # --------------------------------------------------------
    # Optional reservation type filter
    # --------------------------------------------------------

    selected_type = request.GET.get(
        "type",
        "",
    ).strip()

    valid_types = {
        value
        for value, label in Reservation.ReservationType.choices
    }

    if selected_type in valid_types:
        reservations = reservations.filter(
            reservation_type=selected_type,
        )

    # --------------------------------------------------------
    # Optional date filter
    # --------------------------------------------------------

    selected_date = request.GET.get(
        "date",
        "",
    ).strip()

    if selected_date:
        reservations = reservations.filter(
            reservation_date=selected_date,
        )

    reservations = reservations.order_by(
        "-reservation_date",
        "-reservation_time",
    )

    context = {
        "reservations": reservations,
        "status_choices": Reservation.Status.choices,
        "reservation_type_choices": (
            Reservation.ReservationType.choices
        ),
        "selected_status": selected_status,
        "selected_type": selected_type,
        "selected_date": selected_date,
    }

    return render(
        request,
        "management/reservations/manage_reservations_list.html",
        context,
    )


@staff_required
def reservation_detail(request, reservation_id):
    """
    Display complete reservation details.
    """

    reservation = get_object_or_404(
        Reservation,
        pk=reservation_id,
    )

    context = {
        "reservation": reservation,
        "status_choices": Reservation.Status.choices,
    }

    return render(
        request,
        "management/reservations/manage_reservation_detail.html",
        context,
    )


@staff_required
@require_POST
def reservation_status_update(
    request,
    reservation_id,
):
    """
    Update reservation status.

    Deposit payment information is intentionally not modified.
    """

    reservation = get_object_or_404(
        Reservation,
        pk=reservation_id,
    )

    new_status = request.POST.get(
        "status",
        "",
    ).strip()

    valid_statuses = {
        value
        for value, label in Reservation.Status.choices
    }

    if new_status not in valid_statuses:
        messages.error(
            request,
            "Le statut sélectionné est invalide.",
        )

        return redirect(
            "management:reservation_detail",
            reservation_id=reservation.pk,
        )

    if reservation.status == new_status:
        messages.info(
            request,
            "La réservation possède déjà ce statut.",
        )

        return redirect(
            "management:reservation_detail",
            reservation_id=reservation.pk,
        )

    reservation.status = new_status

    reservation.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Le statut de la réservation a été mis à jour.",
    )

    return redirect(
        "management:reservation_detail",
        reservation_id=reservation.pk,
    )


# ============================================================
# CONTACT MESSAGES
# ============================================================

@staff_required
def messages_list(request):
    """
    Display contact messages.
    """

    contact_messages = ContactMessage.objects.all()

    selected_state = request.GET.get(
        "state",
        "",
    ).strip()

    if selected_state == "unread":
        contact_messages = contact_messages.filter(
            is_read=False,
        )

    elif selected_state == "read":
        contact_messages = contact_messages.filter(
            is_read=True,
        )

    contact_messages = contact_messages.order_by(
        "-created_at",
    )

    context = {
        "contact_messages": contact_messages,
        "selected_state": selected_state,
    }

    return render(
        request,
        "management/messages/manage_messages_list.html",
        context,
    )


@staff_required
def message_detail(request, message_id):
    """
    Display one contact message.

    Opening a message automatically marks it as read.
    """

    contact_message = get_object_or_404(
        ContactMessage,
        pk=message_id,
    )

    if not contact_message.is_read:
        contact_message.is_read = True

        contact_message.save(
            update_fields=[
                "is_read",
                "updated_at",
            ]
        )

    context = {
        "contact_message": contact_message,
    }

    return render(
        request,
        "management/messages/manage_message_detail.html",
        context,
    )


@staff_required
@require_POST
def message_toggle_read(request, message_id):
    """
    Toggle a contact message between read and unread.
    """

    contact_message = get_object_or_404(
        ContactMessage,
        pk=message_id,
    )

    contact_message.is_read = not contact_message.is_read

    contact_message.save(
        update_fields=[
            "is_read",
            "updated_at",
        ]
    )

    if contact_message.is_read:
        text = "Le message a été marqué comme lu."
    else:
        text = "Le message a été marqué comme non lu."

    messages.success(
        request,
        text,
    )

    return redirect(
        "management:message_detail",
        message_id=contact_message.pk,
    )


@staff_required
@require_POST
def message_delete(request, message_id):
    """
    Delete a contact message.
    """

    contact_message = get_object_or_404(
        ContactMessage,
        pk=message_id,
    )

    contact_message.delete()

    messages.success(
        request,
        "Le message a été supprimé.",
    )

    return redirect(
        "management:messages_list",
    )


# ============================================================
# DISHES
# ============================================================

@staff_required
def dishes_list(request):
    """
    Display all menu dishes.
    """

    dishes = (
        Dish.objects
        .select_related("category")
        .prefetch_related("allergens")
    )

    selected_category = request.GET.get(
        "category",
        "",
    ).strip()

    selected_availability = request.GET.get(
        "availability",
        "",
    ).strip()

    if selected_category.isdigit():
        dishes = dishes.filter(
            category_id=int(selected_category),
        )

    if selected_availability == "available":
        dishes = dishes.filter(
            is_available=True,
        )

    elif selected_availability == "unavailable":
        dishes = dishes.filter(
            is_available=False,
        )

    context = {
        "dishes": dishes,
        "categories": MenuCategory.objects.all(),
        "selected_category": selected_category,
        "selected_availability": selected_availability,
    }

    return render(
        request,
        "management/menu/manage_dishes_list.html",
        context,
    )


@staff_required
def dish_create(request):
    """
    Create a menu dish.
    """

    if request.method == "POST":
        form = DishManagementForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            dish = form.save()

            messages.success(
                request,
                f'Le plat « {dish.name} » a été ajouté.',
            )

            return redirect(
                "management:dishes_list",
            )

    else:
        form = DishManagementForm()

    return render(
        request,
        "management/menu/manage_dish_form.html",
        {
            "form": form,
            "form_title": "Ajouter un plat",
            "submit_label": "Ajouter le plat",
        },
    )


@staff_required
def dish_update(request, dish_id):
    """
    Update a menu dish.
    """

    dish = get_object_or_404(
        Dish,
        pk=dish_id,
    )

    if request.method == "POST":
        form = DishManagementForm(
            request.POST,
            request.FILES,
            instance=dish,
        )

        if form.is_valid():
            dish = form.save()

            messages.success(
                request,
                f'Le plat « {dish.name} » a été modifié.',
            )

            return redirect(
                "management:dishes_list",
            )

    else:
        form = DishManagementForm(
            instance=dish,
        )

    return render(
        request,
        "management/menu/manage_dish_form.html",
        {
            "form": form,
            "dish": dish,
            "form_title": "Modifier le plat",
            "submit_label": "Enregistrer",
        },
    )


@staff_required
@require_POST
def dish_delete(request, dish_id):
    """
    Delete a dish.

    Historical order items remain valid because OrderItem
    stores dish snapshots and uses SET_NULL.
    """

    dish = get_object_or_404(
        Dish,
        pk=dish_id,
    )

    dish_name = dish.name

    dish.delete()

    messages.success(
        request,
        f'Le plat « {dish_name} » a été supprimé.',
    )

    return redirect(
        "management:dishes_list",
    )


@staff_required
@require_POST
def dish_toggle_availability(request, dish_id):
    """
    Quickly show or hide a dish from ordering.
    """

    dish = get_object_or_404(
        Dish,
        pk=dish_id,
    )

    dish.is_available = not dish.is_available

    dish.save(
        update_fields=[
            "is_available",
            "updated_at",
        ]
    )

    if dish.is_available:
        text = f'« {dish.name} » est maintenant disponible.'
    else:
        text = f'« {dish.name} » est maintenant indisponible.'

    messages.success(
        request,
        text,
    )

    return redirect(
        "management:dishes_list",
    )


# ============================================================
# MENU CATEGORIES
# ============================================================

@staff_required
def categories_list(request):
    """
    Display menu categories.
    """

    categories = (
        MenuCategory.objects
        .annotate(
            dishes_count=models.Count("dishes"),
        )
        .order_by(
            "display_order",
            "name",
        )
    )

    return render(
        request,
        "management/menu/manage_categories_list.html",
        {
            "categories": categories,
        },
    )


@staff_required
def category_create(request):
    """
    Create a menu category.
    """

    if request.method == "POST":
        form = MenuCategoryManagementForm(
            request.POST,
        )

        if form.is_valid():
            category = form.save()

            messages.success(
                request,
                f'La catégorie « {category.name} » a été ajoutée.',
            )

            return redirect(
                "management:categories_list",
            )

    else:
        form = MenuCategoryManagementForm()

    return render(
        request,
        "management/menu/manage_category_form.html",
        {
            "form": form,
            "form_title": "Ajouter une catégorie",
            "submit_label": "Ajouter la catégorie",
        },
    )


@staff_required
def category_update(request, category_id):
    """
    Update a menu category.
    """

    category = get_object_or_404(
        MenuCategory,
        pk=category_id,
    )

    if request.method == "POST":
        form = MenuCategoryManagementForm(
            request.POST,
            instance=category,
        )

        if form.is_valid():
            category = form.save()

            messages.success(
                request,
                f'La catégorie « {category.name} » a été modifiée.',
            )

            return redirect(
                "management:categories_list",
            )

    else:
        form = MenuCategoryManagementForm(
            instance=category,
        )

    return render(
        request,
        "management/menu/manage_category_form.html",
        {
            "form": form,
            "category": category,
            "form_title": "Modifier la catégorie",
            "submit_label": "Enregistrer",
        },
    )


@staff_required
@require_POST
def category_delete(request, category_id):
    """
    Delete an unused category.

    Dish.category uses PROTECT, therefore a category containing
    dishes cannot accidentally be deleted.
    """

    category = get_object_or_404(
        MenuCategory,
        pk=category_id,
    )

    category_name = category.name

    try:
        category.delete()

    except ProtectedError:
        messages.error(
            request,
            (
                f'La catégorie « {category_name} » contient '
                "encore des plats et ne peut pas être supprimée."
            ),
        )

        return redirect(
            "management:categories_list",
        )

    messages.success(
        request,
        f'La catégorie « {category_name} » a été supprimée.',
    )

    return redirect(
        "management:categories_list",
    )


# ============================================================
# ALLERGENS
# ============================================================

@staff_required
def allergens_list(request):
    """
    Display allergens.
    """

    allergens = (
        Allergen.objects
        .annotate(
            dishes_count=models.Count("dishes"),
        )
        .order_by(
            "display_order",
            "name",
        )
    )

    return render(
        request,
        "management/menu/manage_allergens_list.html",
        {
            "allergens": allergens,
        },
    )


@staff_required
def allergen_create(request):
    """
    Create an allergen.
    """

    if request.method == "POST":
        form = AllergenManagementForm(
            request.POST,
        )

        if form.is_valid():
            allergen = form.save()

            messages.success(
                request,
                f'L’allergène « {allergen.name} » a été ajouté.',
            )

            return redirect(
                "management:allergens_list",
            )

    else:
        form = AllergenManagementForm()

    return render(
        request,
        "management/menu/manage_allergen_form.html",
        {
            "form": form,
            "form_title": "Ajouter un allergène",
            "submit_label": "Ajouter l’allergène",
        },
    )


@staff_required
def allergen_update(request, allergen_id):
    """
    Update an allergen.
    """

    allergen = get_object_or_404(
        Allergen,
        pk=allergen_id,
    )

    if request.method == "POST":
        form = AllergenManagementForm(
            request.POST,
            instance=allergen,
        )

        if form.is_valid():
            allergen = form.save()

            messages.success(
                request,
                f'L’allergène « {allergen.name} » a été modifié.',
            )

            return redirect(
                "management:allergens_list",
            )

    else:
        form = AllergenManagementForm(
            instance=allergen,
        )

    return render(
        request,
        "management/menu/manage_allergen_form.html",
        {
            "form": form,
            "allergen": allergen,
            "form_title": "Modifier l’allergène",
            "submit_label": "Enregistrer",
        },
    )


@staff_required
@require_POST
def allergen_delete(request, allergen_id):
    """
    Delete an allergen.

    Removing it also removes its many-to-many associations.
    """

    allergen = get_object_or_404(
        Allergen,
        pk=allergen_id,
    )

    allergen_name = allergen.name

    allergen.delete()

    messages.success(
        request,
        f'L’allergène « {allergen_name} » a été supprimé.',
    )

    return redirect(
        "management:allergens_list",
    )


# ============================================================
# DAILY SPECIALS
# ============================================================

@staff_required
def daily_specials_list(request):
    """
    Display daily specials.
    """

    daily_specials = (
        DailySpecial.objects
        .select_related(
            "dish",
            "dish__category",
        )
        .order_by("-date")
    )

    return render(
        request,
        "management/daily_specials/manage_daily_specials_list.html",
        {
            "daily_specials": daily_specials,
            "today": timezone.localdate(),
        },
    )


@staff_required
def daily_special_create(request):
    """
    Create a daily special.
    """

    if request.method == "POST":
        form = DailySpecialManagementForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            daily_special = form.save()

            messages.success(
                request,
                "Le plat du jour a été ajouté.",
            )

            return redirect(
                "management:daily_specials_list",
            )

    else:
        form = DailySpecialManagementForm(
            initial={
                "date": timezone.localdate(),
            }
        )

    return render(
        request,
        "management/daily_specials/manage_daily_special_form.html",
        {
            "form": form,
            "form_title": "Ajouter un plat du jour",
            "submit_label": "Ajouter",
        },
    )


@staff_required
def daily_special_update(request, special_id):
    """
    Update a daily special.
    """

    daily_special = get_object_or_404(
        DailySpecial,
        pk=special_id,
    )

    if request.method == "POST":
        form = DailySpecialManagementForm(
            request.POST,
            request.FILES,
            instance=daily_special,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Le plat du jour a été modifié.",
            )

            return redirect(
                "management:daily_specials_list",
            )

    else:
        form = DailySpecialManagementForm(
            instance=daily_special,
        )

    return render(
        request,
        "management/daily_specials/manage_daily_special_form.html",
        {
            "form": form,
            "daily_special": daily_special,
            "form_title": "Modifier le plat du jour",
            "submit_label": "Enregistrer",
        },
    )


@staff_required
@require_POST
def daily_special_delete(request, special_id):
    """
    Delete a daily special.
    """

    daily_special = get_object_or_404(
        DailySpecial,
        pk=special_id,
    )

    daily_special.delete()

    messages.success(
        request,
        "Le plat du jour a été supprimé.",
    )

    return redirect(
        "management:daily_specials_list",
    )


@staff_required
@require_POST
def daily_special_toggle_published(
    request,
    special_id,
):
    """
    Publish or hide a daily special.
    """

    daily_special = get_object_or_404(
        DailySpecial,
        pk=special_id,
    )

    daily_special.published = not daily_special.published

    daily_special.save(
        update_fields=[
            "published",
            "updated_at",
        ]
    )

    if daily_special.published:
        text = "Le plat du jour est maintenant publié."
    else:
        text = "Le plat du jour a été masqué."

    messages.success(
        request,
        text,
    )

    return redirect(
        "management:daily_specials_list",
    )


# ============================================================
# DELIVERY ZONES
# ============================================================

@staff_required
def delivery_zones_list(request):
    """
    Display delivery zones.
    """

    delivery_zones = DeliveryZone.objects.order_by(
        "postal_code",
        "city",
    )

    return render(
        request,
        "management/delivery/manage_delivery_zones_list.html",
        {
            "delivery_zones": delivery_zones,
        },
    )


@staff_required
def delivery_zone_create(request):
    """
    Create a delivery zone.
    """

    if request.method == "POST":
        form = DeliveryZoneManagementForm(
            request.POST,
        )

        if form.is_valid():
            zone = form.save()

            messages.success(
                request,
                f'La zone « {zone} » a été ajoutée.',
            )

            return redirect(
                "management:delivery_zones_list",
            )

    else:
        form = DeliveryZoneManagementForm()

    return render(
        request,
        "management/delivery/manage_delivery_zone_form.html",
        {
            "form": form,
            "form_title": "Ajouter une zone de livraison",
            "submit_label": "Ajouter la zone",
        },
    )


@staff_required
def delivery_zone_update(request, zone_id):
    """
    Update a delivery zone.
    """

    zone = get_object_or_404(
        DeliveryZone,
        pk=zone_id,
    )

    if request.method == "POST":
        form = DeliveryZoneManagementForm(
            request.POST,
            instance=zone,
        )

        if form.is_valid():
            zone = form.save()

            messages.success(
                request,
                f'La zone « {zone} » a été modifiée.',
            )

            return redirect(
                "management:delivery_zones_list",
            )

    else:
        form = DeliveryZoneManagementForm(
            instance=zone,
        )

    return render(
        request,
        "management/delivery/manage_delivery_zone_form.html",
        {
            "form": form,
            "zone": zone,
            "form_title": "Modifier la zone de livraison",
            "submit_label": "Enregistrer",
        },
    )


@staff_required
@require_POST
def delivery_zone_delete(request, zone_id):
    """
    Delete a delivery zone.

    Existing orders keep their history because Order.delivery_zone
    uses SET_NULL and delivery_fee is stored directly on the order.
    """

    zone = get_object_or_404(
        DeliveryZone,
        pk=zone_id,
    )

    zone_name = str(zone)

    zone.delete()

    messages.success(
        request,
        f'La zone « {zone_name} » a été supprimée.',
    )

    return redirect(
        "management:delivery_zones_list",
    )


@staff_required
@require_POST
def delivery_zone_toggle_active(request, zone_id):
    """
    Enable or disable a delivery zone.
    """

    zone = get_object_or_404(
        DeliveryZone,
        pk=zone_id,
    )

    zone.is_active = not zone.is_active

    zone.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    if zone.is_active:
        text = f'La zone « {zone} » est maintenant active.'
    else:
        text = f'La zone « {zone} » a été désactivée.'

    messages.success(
        request,
        text,
    )

    return redirect(
        "management:delivery_zones_list",
    )


# ============================================================
# EVENTS
# ============================================================

@staff_required
def events_list(request):
    """
    Display restaurant events.
    """

    events = Event.objects.order_by(
        "-start_at",
    )

    return render(
        request,
        "management/events/manage_events_list.html",
        {
            "events": events,
            "now": timezone.now(),
        },
    )


@staff_required
def event_create(request):
    """
    Create an event.
    """

    if request.method == "POST":
        form = EventManagementForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            event = form.save()

            messages.success(
                request,
                f'L’événement « {event.title} » a été ajouté.',
            )

            return redirect(
                "management:events_list",
            )

    else:
        form = EventManagementForm()

    return render(
        request,
        "management/events/manage_event_form.html",
        {
            "form": form,
            "form_title": "Ajouter un événement",
            "submit_label": "Ajouter l’événement",
        },
    )


@staff_required
def event_update(request, event_id):
    """
    Update an event.
    """

    event = get_object_or_404(
        Event,
        pk=event_id,
    )

    if request.method == "POST":
        form = EventManagementForm(
            request.POST,
            request.FILES,
            instance=event,
        )

        if form.is_valid():
            event = form.save()

            messages.success(
                request,
                f'L’événement « {event.title} » a été modifié.',
            )

            return redirect(
                "management:events_list",
            )

    else:
        form = EventManagementForm(
            instance=event,
        )

    return render(
        request,
        "management/events/manage_event_form.html",
        {
            "form": form,
            "event": event,
            "form_title": "Modifier l’événement",
            "submit_label": "Enregistrer",
        },
    )


@staff_required
@require_POST
def event_delete(request, event_id):
    """
    Delete an event.
    """

    event = get_object_or_404(
        Event,
        pk=event_id,
    )

    event_title = event.title

    event.delete()

    messages.success(
        request,
        f'L’événement « {event_title} » a été supprimé.',
    )

    return redirect(
        "management:events_list",
    )


@staff_required
@require_POST
def event_toggle_published(request, event_id):
    """
    Publish or hide an event.
    """

    event = get_object_or_404(
        Event,
        pk=event_id,
    )

    event.is_published = not event.is_published

    event.save(
        update_fields=[
            "is_published",
            "updated_at",
        ]
    )

    if event.is_published:
        text = f'L’événement « {event.title} » est publié.'
    else:
        text = f'L’événement « {event.title} » a été masqué.'

    messages.success(
        request,
        text,
    )

    return redirect(
        "management:events_list",
    )


# ============================================================
# GALLERY - ALBUMS
# ============================================================

@staff_required
def gallery_albums_list(request):
    """
    Display gallery albums.
    """

    albums = (
        GalleryAlbum.objects
        .annotate(
            images_count=models.Count("images"),
        )
        .order_by(
            "display_order",
            "-is_featured",
            "-created_at",
        )
    )

    return render(
        request,
        "management/gallery/manage_gallery_albums_list.html",
        {
            "albums": albums,
        },
    )


@staff_required
def gallery_album_detail(request, album_id):
    """
    Display an album and all its images.
    """

    album = get_object_or_404(
        GalleryAlbum,
        pk=album_id,
    )

    gallery_images = album.images.all().order_by(
        "display_order",
        "-created_at",
    )

    return render(
        request,
        "management/gallery/manage_gallery_album_detail.html",
        {
            "album": album,
            "images": gallery_images,
        },
    )


@staff_required
def gallery_album_create(request):
    """
    Create a gallery album.
    """

    if request.method == "POST":
        form = GalleryAlbumManagementForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            album = form.save()

            messages.success(
                request,
                f'L’album « {album.title} » a été ajouté.',
            )

            return redirect(
                "management:gallery_album_detail",
                album_id=album.pk,
            )

    else:
        form = GalleryAlbumManagementForm()

    return render(
        request,
        "management/gallery/manage_gallery_album_form.html",
        {
            "form": form,
            "form_title": "Ajouter un album",
            "submit_label": "Créer l’album",
        },
    )


@staff_required
def gallery_album_update(request, album_id):
    """
    Update a gallery album.
    """

    album = get_object_or_404(
        GalleryAlbum,
        pk=album_id,
    )

    if request.method == "POST":
        form = GalleryAlbumManagementForm(
            request.POST,
            request.FILES,
            instance=album,
        )

        if form.is_valid():
            album = form.save()

            messages.success(
                request,
                f'L’album « {album.title} » a été modifié.',
            )

            return redirect(
                "management:gallery_album_detail",
                album_id=album.pk,
            )

    else:
        form = GalleryAlbumManagementForm(
            instance=album,
        )

    return render(
        request,
        "management/gallery/manage_gallery_album_form.html",
        {
            "form": form,
            "album": album,
            "form_title": "Modifier l’album",
            "submit_label": "Enregistrer",
        },
    )


@staff_required
@require_POST
def gallery_album_delete(request, album_id):
    """
    Delete a gallery album and its associated images.
    """

    album = get_object_or_404(
        GalleryAlbum,
        pk=album_id,
    )

    album_title = album.title

    album.delete()

    messages.success(
        request,
        f'L’album « {album_title} » a été supprimé.',
    )

    return redirect(
        "management:gallery_albums_list",
    )


# ============================================================
# GALLERY - IMAGES
# ============================================================

@staff_required
def gallery_image_create(request, album_id):
    """
    Add an image to a gallery album.
    """

    album = get_object_or_404(
        GalleryAlbum,
        pk=album_id,
    )

    if request.method == "POST":
        form = GalleryImageManagementForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            gallery_image = form.save(
                commit=False,
            )

            gallery_image.album = album
            gallery_image.save()

            messages.success(
                request,
                "L’image a été ajoutée à l’album.",
            )

            return redirect(
                "management:gallery_album_detail",
                album_id=album.pk,
            )

    else:
        form = GalleryImageManagementForm()

    return render(
        request,
        "management/gallery/manage_gallery_image_form.html",
        {
            "form": form,
            "album": album,
            "form_title": "Ajouter une image",
            "submit_label": "Ajouter l’image",
        },
    )


@staff_required
def gallery_image_update(request, image_id):
    """
    Update a gallery image.
    """

    gallery_image = get_object_or_404(
        GalleryImage.objects.select_related("album"),
        pk=image_id,
    )

    if request.method == "POST":
        form = GalleryImageManagementForm(
            request.POST,
            request.FILES,
            instance=gallery_image,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "L’image a été modifiée.",
            )

            return redirect(
                "management:gallery_album_detail",
                album_id=gallery_image.album_id,
            )

    else:
        form = GalleryImageManagementForm(
            instance=gallery_image,
        )

    return render(
        request,
        "management/gallery/manage_gallery_image_form.html",
        {
            "form": form,
            "gallery_image": gallery_image,
            "album": gallery_image.album,
            "form_title": "Modifier l’image",
            "submit_label": "Enregistrer",
        },
    )


@staff_required
@require_POST
def gallery_image_delete(request, image_id):
    """
    Delete a gallery image.
    """

    gallery_image = get_object_or_404(
        GalleryImage,
        pk=image_id,
    )

    album_id = gallery_image.album_id

    gallery_image.delete()

    messages.success(
        request,
        "L’image a été supprimée.",
    )

    return redirect(
        "management:gallery_album_detail",
        album_id=album_id,
    )


# ============================================================
# SITE SETTINGS
# ============================================================

@staff_required
def site_settings(request):
    """
    Edit the restaurant's global settings.

    The management interface treats SiteSettings as a singleton.
    """

    settings_object = SiteSettings.objects.first()

    if settings_object is None:
        settings_object = SiteSettings()

    if request.method == "POST":
        form = SiteSettingsManagementForm(
            request.POST,
            instance=settings_object,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Les paramètres du site ont été enregistrés.",
            )

            return redirect(
                "management:site_settings",
            )

    else:
        form = SiteSettingsManagementForm(
            instance=settings_object,
        )

    return render(
        request,
        "management/settings/manage_site_settings.html",
        {
            "form": form,
            "site_settings": settings_object,
        },
    )
    
    

@staff_member_required(login_url="/gestion/login/")
def manage_promotions_list(request):
    promotions = Promotion.objects.all()

    return render(
        request,
        "management/promotions/manage_promotions_list.html",
        {"promotions": promotions},
    )


@staff_member_required(login_url="/gestion/login/")
def manage_promotion_create(request):
    form = PromotionManagementForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Promotion créée avec succès.")
        return redirect("management:promotions_list")

    return render(
        request,
        "management/promotions/manage_promotion_form.html",
        {
            "form": form,
            "page_title": "Nouvelle promotion",
            "is_edit": False,
        },
    )


@staff_member_required(login_url="/gestion/login/")
def manage_promotion_update(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)

    form = PromotionManagementForm(
        request.POST or None,
        request.FILES or None,
        instance=promotion,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Promotion modifiée avec succès.")
        return redirect("management:promotions_list")

    return render(
        request,
        "management/promotions/manage_promotion_form.html",
        {
            "form": form,
            "promotion": promotion,
            "page_title": "Modifier la promotion",
            "is_edit": True,
        },
    )


@staff_member_required(login_url="/gestion/login/")
@require_POST
def manage_promotion_toggle(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)

    promotion.is_active = not promotion.is_active
    promotion.save(update_fields=["is_active", "updated_at"])

    messages.success(
        request,
        "Statut de la promotion mis à jour.",
    )
    return redirect("management:promotions_list")
