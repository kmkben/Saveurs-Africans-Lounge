from django.db import models
from django.urls import reverse
from django.utils.text import slugify

# Create your models here.


class MenuCategory(models.Model):
    """
    Groups dishes into sections such as:
    Entrées, Plats, Desserts, Boissons, etc.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom",
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="Les catégories avec le plus petit numéro apparaissent en premier.",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Visible",
        help_text="Décochez pour masquer cette catégorie sur le site.",
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
        verbose_name = "Catégorie du menu"
        verbose_name_plural = "Catégories du menu"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()

        super().save(*args, **kwargs)

    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        while MenuCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug


class Allergen(models.Model):
    """
    Allergens that can be associated with one or several dishes.

    Examples:
    Gluten, arachides, lait, œufs, poisson, fruits à coque, etc.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Icône",
        help_text=(
            "Classe d'icône facultative, par exemple : "
            "'fa-solid fa-wheat-awn'."
        ),
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
    )

    class Meta:
        verbose_name = "Allergène"
        verbose_name_plural = "Allergènes"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Dish(models.Model):
    """
    A dish or drink displayed on the restaurant menu.
    """

    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.PROTECT,
        related_name="dishes",
        verbose_name="Catégorie",
    )

    name = models.CharField(
        max_length=150,
        verbose_name="Nom",
    )

    slug = models.SlugField(
        max_length=170,
        unique=True,
        blank=True,
    )

    short_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Description courte",
        help_text="Résumé affiché directement sur la carte.",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description détaillée",
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Prix",
    )

    image = models.ImageField(
        upload_to="menu/dishes/",
        blank=True,
        null=True,
        verbose_name="Photo",
    )

    allergens = models.ManyToManyField(
        Allergen,
        blank=True,
        related_name="dishes",
        verbose_name="Allergènes",
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="Disponible",
        help_text=(
            "Décochez cette case pour masquer temporairement "
            "le plat du menu et des commandes."
        ),
    )

    is_delivery_available = models.BooleanField(
        default=True,
        verbose_name="Disponible en livraison",
        help_text="Indique si ce plat peut être commandé en livraison.",
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Mis en avant",
        help_text="Le plat pourra apparaître dans les sélections du site.",
    )
    
    is_new = models.BooleanField(
        default=False,
        verbose_name="Nouveauté",
        help_text="Mettre en avant ce produit dans les nouveautés.",
    )

    new_from = models.DateField(
        blank=True,
        null=True,
        verbose_name="Nouveauté à partir du",
    )

    new_until = models.DateField(
        blank=True,
        null=True,
        verbose_name="Nouveauté jusqu'au",
    )

    is_today_special = models.BooleanField(
        default=False,
        verbose_name="Plat du jour",
        help_text="Affiche ce plat dans la section des plats du jour.",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="Les plats avec le plus petit numéro apparaissent en premier.",
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
        verbose_name = "Plat"
        verbose_name_plural = "Plats"
        ordering = [
            "category__display_order",
            "display_order",
            "name",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="unique_dish_name_per_category",
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()

        super().save(*args, **kwargs)

    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        while Dish.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def get_absolute_url(self):
        return reverse(
            "menu:dish_detail",
            kwargs={"slug": self.slug},
        )

    @property
    def active_allergens(self):
        return self.allergens.filter(is_active=True)