from django.urls import path

from .views import (
    GalleryAlbumDetailView,
    GalleryAlbumListView,
)


app_name = "gallery"


urlpatterns = [
    path(
        "",
        GalleryAlbumListView.as_view(),
        name="albums",
    ),
    path(
        "<slug:slug>/",
        GalleryAlbumDetailView.as_view(),
        name="album_detail",
    ),
]