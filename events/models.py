from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Event(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Titre",
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
    )

    short_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Courte description",
    )

    description = models.TextField(
        verbose_name="Description",
    )

    image = models.ImageField(
        upload_to="events/",
        blank=True,
        null=True,
        verbose_name="Image",
    )

    start_at = models.DateTimeField(
        verbose_name="Date et heure de début",
    )

    end_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date et heure de fin",
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Lieu",
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Prix",
        help_text="Laisser vide si l’événement est gratuit.",
    )

    reservation_required = models.BooleanField(
        default=False,
        verbose_name="Réservation obligatoire",
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Événement mis en avant",
    )

    is_published = models.BooleanField(
        default=True,
        verbose_name="Publié",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le",
    )

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ("start_at",)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "events:detail",
            kwargs={"slug": self.slug},
        )

    @property
    def is_free(self):
        return self.price is None or self.price == 0