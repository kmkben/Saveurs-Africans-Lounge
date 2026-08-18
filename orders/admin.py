from django.contrib import admin

from .models import Order, OrderItem, DeliveryZone


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    fields = (
        "dish",
        "dish_name",
        "unit_price",
        "quantity",
        "note",
        "display_total",
    )

    readonly_fields = (
        "dish",
        "dish_name",
        "unit_price",
        "display_total",
    )

    can_delete = False

    @admin.display(description="Total")
    def display_total(self, obj):
        if not obj.pk:
            return "—"

        return f"{obj.total_price:.2f} €"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "order_type",
        "display_total",
        "status",
        "payment_status",
        "payment_method",
        "created_at",
    )

    list_display_links = (
        "id",
        "customer_name",
    )

    list_editable = (
        "status",
        "payment_status",
    )

    list_filter = (
        "status",
        "payment_status",
        "payment_method",
        "order_type",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "email",
        "phone",
        "payment_reference",
        "items__dish_name",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "display_subtotal",
        "display_total",
        "amount_paid",
        "payment_reference",
        "paid_at",
        "created_at",
        "updated_at",
    )

    inlines = (
        OrderItemInline,
    )

    fieldsets = (
        (
            "Commande",
            {
                "fields": (
                    "status",
                    "order_type",
                    "customer_note",
                ),
            },
        ),
        (
            "Client",
            {
                "fields": (
                    "customer_name",
                    "email",
                    "phone",
                ),
            },
        ),
        (
            "Livraison",
            {
                "fields": (
                    "address",
                    "address_complement",
                    "postal_code",
                    "city",
                    "delivery_fee",
                ),
            },
        ),
        (
            "Paiement",
            {
                "fields": (
                    "payment_method",
                    "payment_status",
                    "display_subtotal",
                    "display_total",
                    "amount_paid",
                    "payment_reference",
                    "paid_at",
                ),
            },
        ),
        (
            "Informations système",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(description="Sous-total")
    def display_subtotal(self, obj):
        if not obj.pk:
            return "—"

        return f"{obj.subtotal:.2f} €"

    @admin.display(description="Total")
    def display_total(self, obj):
        if not obj.pk:
            return "—"

        return f"{obj.total:.2f} €"
    
    
@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = (
        "postal_code",
        "city",
        "delivery_fee",
        "minimum_order",
        "free_delivery_from",
        "is_active",
    )

    list_editable = (
        "delivery_fee",
        "minimum_order",
        "free_delivery_from",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "postal_code",
        "city",
        "name",
    )

    ordering = (
        "postal_code",
        "city",
    )