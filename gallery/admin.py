from django.contrib import admin
from django.utils.html import format_html

from .models import GalleryAlbum, GalleryImage


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 1

    fields = (
        "image",
        "title",
        "caption",
        "display_order",
        "is_published",
    )

    ordering = (
        "display_order",
        "-created_at",
    )


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = (
        "cover_preview",
        "title",
        "category",
        "published_images_count",
        "display_order",
        "is_featured",
        "is_published",
    )

    list_display_links = (
        "title",
    )

    list_editable = (
        "display_order",
        "is_featured",
        "is_published",
    )

    list_filter = (
        "category",
        "is_featured",
        "is_published",
    )

    search_fields = (
        "title",
        "description",
    )

    ordering = (
        "display_order",
        "-is_featured",
        "-created_at",
    )

    readonly_fields = (
        "slug",
        "large_cover_preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Album information",
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "category",
                )
            },
        ),
        (
            "Cover",
            {
                "fields": (
                    "cover_image",
                    "large_cover_preview",
                )
            },
        ),
        (
            "Publication",
            {
                "fields": (
                    "display_order",
                    "is_featured",
                    "is_published",
                )
            },
        ),
        (
            "Dates",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    inlines = (
        GalleryImageInline,
    )

    @admin.display(description="Cover")
    def cover_preview(self, obj):
        if not obj.cover_image:
            return "—"

        return format_html(
            '<img src="{}" style="width:75px;height:55px;'
            'object-fit:cover;border-radius:5px;">',
            obj.cover_image.url,
        )

    @admin.display(description="Cover preview")
    def large_cover_preview(self, obj):
        if not obj.pk or not obj.cover_image:
            return "The preview will appear after saving the album."

        return format_html(
            '<img src="{}" style="max-width:520px;'
            'max-height:350px;object-fit:cover;border-radius:6px;">',
            obj.cover_image.url,
        )


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = (
        "image_preview",
        "title",
        "album",
        "display_order",
        "is_published",
    )

    list_display_links = (
        "title",
    )

    list_editable = (
        "display_order",
        "is_published",
    )

    list_filter = (
        "album",
        "is_published",
    )

    search_fields = (
        "title",
        "caption",
        "album__title",
    )

    autocomplete_fields = (
        "album",
    )

    readonly_fields = (
        "large_image_preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Image",
            {
                "fields": (
                    "album",
                    "title",
                    "image",
                    "large_image_preview",
                    "caption",
                )
            },
        ),
        (
            "Publication",
            {
                "fields": (
                    "display_order",
                    "is_published",
                )
            },
        ),
        (
            "Dates",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not obj.image:
            return "—"

        return format_html(
            '<img src="{}" style="width:75px;height:55px;'
            'object-fit:cover;border-radius:5px;">',
            obj.image.url,
        )

    @admin.display(description="Image preview")
    def large_image_preview(self, obj):
        if not obj.pk or not obj.image:
            return "The preview will appear after saving the image."

        return format_html(
            '<img src="{}" style="max-width:520px;'
            'max-height:350px;object-fit:cover;border-radius:6px;">',
            obj.image.url,
        )