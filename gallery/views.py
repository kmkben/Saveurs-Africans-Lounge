from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.views.generic import DetailView, ListView

from .models import GalleryAlbum, GalleryImage


class GalleryAlbumListView(ListView):
    model = GalleryAlbum
    template_name = "gallery/album_list.html"
    context_object_name = "albums"

    def get_queryset(self):
        queryset = (
            GalleryAlbum.objects
            .filter(is_published=True)
            .annotate(
                visible_images_count=Count(
                    "images",
                    filter=Q(images__is_published=True),
                )
            )
        )

        category = self.request.GET.get("category")

        valid_categories = {
            choice.value
            for choice in GalleryAlbum.Category
        }

        if category in valid_categories:
            queryset = queryset.filter(category=category)

        return queryset.order_by(
            "display_order",
            "-is_featured",
            "-created_at",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["categories"] = GalleryAlbum.Category.choices
        context["selected_category"] = self.request.GET.get(
            "category",
            "",
        )

        return context


class GalleryAlbumDetailView(DetailView):
    model = GalleryAlbum
    template_name = "gallery/album_detail.html"
    context_object_name = "album"

    def get_queryset(self):
        return GalleryAlbum.objects.filter(
            is_published=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        images_queryset = GalleryImage.objects.filter(
            album=self.object,
            is_published=True,
        ).order_by(
            "display_order",
            "-created_at",
        )

        paginator = Paginator(
            images_queryset,
            12,
        )

        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["images"] = page_obj.object_list
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["is_paginated"] = page_obj.has_other_pages()

        return context