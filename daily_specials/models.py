from django.db import models


class DailySpecial(models.Model):
    dish = models.ForeignKey(
        "menu.Dish",
        on_delete=models.CASCADE,
        related_name="daily_specials",
        verbose_name="Plat",
    )

    date = models.DateField(
        unique=True,
        verbose_name="Date",
    )

    special_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Prix du jour",
    )

    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Information complémentaire",
        help_text=(
            "Exemple : servi avec riz parfumé et bissap."
        ),
    )
    
    image = models.ImageField(
        upload_to="daily_specials/",
        blank=True,
        null=True,
        verbose_name="Image de l'offre",
        help_text=(
            "Image spécifique au plat du jour. "
            "Si aucune image n’est ajoutée, l’image du plat sera utilisée."
        ),
    )

    published = models.BooleanField(
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
        verbose_name = "Plat du jour"
        verbose_name_plural = "Plats du jour"
        ordering = ("-date",)

    def __str__(self):
        return f"{self.date} — {self.dish.name}"

    @property
    def price(self):
        return self.special_price or self.dish.price
    
    
    @property
    def display_image(self):
        if self.image:
            return self.image

        return self.dish.image