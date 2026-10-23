from decimal import Decimal

from django.db import models



class DeliveryZone(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Zone",
    )

    postal_code = models.CharField(
        max_length=20,
        verbose_name="Code postal",
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ville",
    )

    delivery_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Frais de livraison",
    )

    minimum_order = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Commande minimum",
    )

    free_delivery_from = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Livraison offerte à partir de",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créée le",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifiée le",
    )

    class Meta:
        verbose_name = "Zone de livraison"
        verbose_name_plural = "Zones de livraison"
        ordering = ("postal_code", "city")

    def __str__(self):
        if self.city:
            return f"{self.postal_code} — {self.city}"

        return self.postal_code


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        CONFIRMED = "CONFIRMED", "Confirmée"
        PREPARING = "PREPARING", "En préparation"
        READY = "READY", "Prête"
        OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", "En livraison"
        COMPLETED = "COMPLETED", "Terminée"
        CANCELLED = "CANCELLED", "Annulée"

    class OrderType(models.TextChoices):
        DELIVERY = "DELIVERY", "Livraison"
        PICKUP = "PICKUP", "À emporter"

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "En attente"
        PAID = "PAID", "Payée"
        FAILED = "FAILED", "Échouée"
        REFUNDED = "REFUNDED", "Remboursée"

    class PaymentMethod(models.TextChoices):
        ONLINE = "ONLINE", "Paiement en ligne"
        CASH = "CASH", "Paiement à la livraison / au retrait"

    # --------------------------------------------------
    # Customer
    # --------------------------------------------------

    customer_name = models.CharField(
        max_length=150,
        verbose_name="Nom complet",
    )

    email = models.EmailField(
        blank=True,
        verbose_name="Adresse e-mail",
    )

    phone = models.CharField(
        max_length=30,
        verbose_name="Téléphone",
    )

    # --------------------------------------------------
    # Order
    # --------------------------------------------------

    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.DELIVERY,
        verbose_name="Mode de commande",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Statut",
    )

    customer_note = models.TextField(
        blank=True,
        verbose_name="Instructions",
        help_text=(
            "Exemple : sans piment, sauce à part, "
            "sonner à l’interphone..."
        ),
    )

    # --------------------------------------------------
    # Delivery
    # --------------------------------------------------
    
    

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Adresse",
    )

    address_complement = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Complément d’adresse",
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Code postal",
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ville",
    )
    
    delivery_zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Zone de livraison",
    )

    delivery_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Frais de livraison",
    )

    # --------------------------------------------------
    # Payment
    # --------------------------------------------------

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name="Mode de paiement",
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Statut du paiement",
    )

    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Référence de paiement",
    )

    amount_paid = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Montant payé",
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Payée le",
    )
    
    # notifications_sent = models.BooleanField(
    #     default=False,
    #     verbose_name="Notifications envoyées",
    # )
    
    email_notifications_sent = models.BooleanField(
        default=False,
        verbose_name="Notifications e-mail envoyées",
    )

    sms_notifications_sent = models.BooleanField(
        default=False,
        verbose_name="Notifications SMS envoyées",
    )

    # --------------------------------------------------
    # Dates
    # --------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créée le",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifiée le",
    )

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Commande #{self.pk} — {self.customer_name}"

    @property
    def subtotal(self):
        return sum(
            (item.total_price for item in self.items.all()),
            Decimal("0.00"),
        )

    @property
    def total(self):
        return self.subtotal + self.delivery_fee

    @property
    def is_paid(self):
        return self.payment_status == self.PaymentStatus.PAID


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Commande",
    )

    dish = models.ForeignKey(
        "menu.Dish",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Plat",
    )

    # Snapshots: preserve order history even if the dish changes later.
    dish_name = models.CharField(
        max_length=180,
        verbose_name="Nom du plat",
    )

    unit_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Prix unitaire",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantité",
    )

    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Instruction",
        help_text="Exemple : sans piment, sauce à part...",
    )
    
        
    is_promotional_gift = models.BooleanField(
        default=False,
        verbose_name="Cadeau promotionnel",
    )

    promotion = models.ForeignKey(
        "promotions.Promotion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Promotion",
    )

    promotion_name = models.CharField(
        max_length=180,
        blank=True,
        verbose_name="Nom de la promotion",
    )


    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"

    def __str__(self):
        return f"{self.quantity} × {self.dish_name}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity
    
    
    

