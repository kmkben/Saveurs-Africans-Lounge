
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class PromotionQuerySet(models.QuerySet):
    def active(self):
        today = timezone.localdate()

        return self.filter(
            is_active=True,
            starts_on__lte=today,
            ends_on__gte=today,
        )


class Promotion(models.Model):
    title = models.CharField(
        max_length=180,
        verbose_name="Titre",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    image = models.ImageField(
        upload_to="promotions/",
        blank=True,
        null=True,
        verbose_name="Image",
    )

    starts_on = models.DateField(
        verbose_name="Date de début",
    )

    ends_on = models.DateField(
        verbose_name="Date de fin",
    )

    is_active = models.BooleanField(
        default=False,
        verbose_name="Promotion active",
    )

    minimum_subtotal = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Montant minimum de commande",
    )

    eligible_dishes = models.ManyToManyField(
        "menu.Dish",
        blank=True,
        related_name="eligible_promotions",
        verbose_name="Plats concernés",
        help_text=(
            "Laissez vide pour rendre tous les plats "
            "disponibles éligibles."
        ),
    )

    gift_dishes = models.ManyToManyField(
        "menu.Dish",
        related_name="gift_promotions",
        verbose_name="Cadeaux proposés",
        help_text=(
            "Exemple : bissap, jus de gingembre, entrée."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = PromotionQuerySet.as_manager()

    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ("-starts_on", "-created_at")
        constraints = [
            models.CheckConstraint(
                condition=Q(minimum_subtotal__gte=0),
                name="promotion_nonnegative_minimum",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        if (
            self.starts_on
            and self.ends_on
            and self.ends_on < self.starts_on
        ):
            raise ValidationError({
                "ends_on": (
                    "La date de fin doit être postérieure "
                    "à la date de début."
                )
            })
