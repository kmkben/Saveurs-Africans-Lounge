from django.core.validators import MinValueValidator
from django.db import models


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        CONFIRMED = "CONFIRMED", "Confirmée"
        CANCELLED = "CANCELLED", "Annulée"
        COMPLETED = "COMPLETED", "Terminée"

    first_name = models.CharField(
        max_length=100,
        verbose_name="Prénom",
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name="Nom",
    )

    email = models.EmailField(
        verbose_name="Adresse e-mail",
    )

    phone = models.CharField(
        max_length=30,
        verbose_name="Téléphone",
    )

    reservation_date = models.DateField(
        verbose_name="Date",
    )

    reservation_time = models.TimeField(
        verbose_name="Heure",
    )

    number_of_guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre de personnes",
    )

    special_request = models.TextField(
        blank=True,
        verbose_name="Demande particulière",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Statut",
    )

    requires_deposit = models.BooleanField(
        default=False,
        verbose_name="Acompte requis",
    )

    deposit_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Montant de l'acompte",
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
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ["reservation_date", "reservation_time"]

    def __str__(self):
        return (
            f"{self.first_name} {self.last_name} — "
            f"{self.reservation_date} à {self.reservation_time}"
        )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"