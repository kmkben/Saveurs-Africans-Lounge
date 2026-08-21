from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class SiteSettings(models.Model):
    restaurant_name = models.CharField(
        max_length=150,
        default="Saveurs Africans Lounge",
        verbose_name="Nom du restaurant",
    )

    tagline = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Slogan",
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Téléphone",
    )

    email = models.EmailField(
        blank=True,
        verbose_name="Adresse e-mail",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Adresse",
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

    google_maps_url = models.URLField(
        blank=True,
        verbose_name="Lien Google Maps",
    )

    facebook_url = models.URLField(
        blank=True,
        verbose_name="Lien Facebook",
    )

    instagram_url = models.URLField(
        blank=True,
        verbose_name="Lien Instagram",
    )

    tiktok_url = models.URLField(
        blank=True,
        verbose_name="Lien TikTok",
    )

    opening_hours = models.TextField(
        blank=True,
        verbose_name="Horaires d’ouverture",
    )

    reservation_deposit_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("15.00"),
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
        verbose_name="Acompte de réservation",
        help_text=(
            "Montant demandé pour toute réservation de table."
        ),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le",
    )

    class Meta:
        verbose_name = "Paramètres du site"
        verbose_name_plural = "Paramètres du site"

    def __str__(self):
        return self.restaurant_name