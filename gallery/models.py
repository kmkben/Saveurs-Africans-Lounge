from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class GalleryAlbum(models.Model):
    class Category(models.TextChoices):
        FOOD = "FOOD", "Plats"
        RESTAURANT = "RESTAURANT", "Restaurant"
        EVENTS = "EVENTS", "Événements"
        PRIVATE_ROOM = "PRIVATE_ROOM", "Salle privée"
        TEAM = "TEAM", "Équipe"
        OTHER = "OTHER", "Autres"

    title = models.CharField(
        max_length=180,
        verbose_name="Title",
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        verbose_name="Slug",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    cover_image = models.ImageField(
        upload_to="gallery/albums/",
        verbose_name="Cover image",
    )

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.RESTAURANT,
        verbose_name="Category",
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Featured",
    )

    is_published = models.BooleanField(
        default=True,
        verbose_name="Published",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Display order",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    class Meta:
        verbose_name = "Gallery album"
        verbose_name_plural = "Gallery albums"
        ordering = (
            "display_order",
            "-is_featured",
            "-created_at",
        )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 2

            while GalleryAlbum.objects.filter(
                slug=slug,
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "gallery:album_detail",
            kwargs={"slug": self.slug},
        )

    @property
    def published_images_count(self):
        return self.images.filter(is_published=True).count()


class GalleryImage(models.Model):
    album = models.ForeignKey(
        GalleryAlbum,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Album",
    )

    title = models.CharField(
        max_length=180,
        blank=True,
        verbose_name="Title",
    )

    image = models.ImageField(
        upload_to="gallery/images/",
        verbose_name="Image",
    )

    caption = models.TextField(
        blank=True,
        verbose_name="Caption",
    )

    is_published = models.BooleanField(
        default=True,
        verbose_name="Published",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Display order",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    class Meta:
        verbose_name = "Gallery image"
        verbose_name_plural = "Gallery images"
        ordering = (
            "display_order",
            "-created_at",
        )

    def __str__(self):
        return self.title or f"Image from {self.album.title}"