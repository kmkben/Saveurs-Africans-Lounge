from django.urls import path

from .views import ContactCreateView, ContactSuccessView


app_name = "contact"


urlpatterns = [
    path(
        "",
        ContactCreateView.as_view(),
        name="contact",
    ),
    path(
        "message-envoye/",
        ContactSuccessView.as_view(),
        name="success",
    ),
]