from django.db import models


class ContactMessage(models.Model):
    class Subject(models.TextChoices):
        INFORMATION = (
            "INFORMATION",
            "Demande d’information",
        )
        RESERVATION = (
            "RESERVATION",
            "Réservation",
        )
        PRIVATE_ROOM = (
            "PRIVATE_ROOM",
            "Salle privée",
        )
        EVENT = (
            "EVENT",
            "Organisation d’un événement",
        )
        PARTNERSHIP = (
            "PARTNERSHIP",
            "Partenariat",
        )
        OTHER = (
            "OTHER",
            "Autre",
        )

    name = models.CharField(
        max_length=150,
        verbose_name="Nom complet",
    )

    email = models.EmailField(
        verbose_name="Adresse e-mail",
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Téléphone",
    )

    subject = models.CharField(
        max_length=30,
        choices=Subject.choices,
        default=Subject.INFORMATION,
        verbose_name="Sujet",
    )

    subject_detail = models.CharField(
        max_length=180,
        blank=True,
        verbose_name="Précision",
        help_text=(
            "Ajoutez une précision si nécessaire, "
            "par exemple : anniversaire pour 20 personnes."
        ),
    )

    message = models.TextField(
        verbose_name="Message",
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="Lu",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Reçu le",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le",
    )

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ("-created_at",)

    def __str__(self):
        subject_label = self.get_subject_display()

        if self.subject_detail:
            return (
                f"{self.name} — "
                f"{subject_label}: {self.subject_detail}"
            )

        return f"{self.name} — {subject_label}"