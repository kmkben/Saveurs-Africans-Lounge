from django.urls import path

from . import views


app_name = "orders"


urlpatterns = [
    path(
        "panier/",
        views.cart_detail,
        name="cart",
    ),
    path(
        "panier/ajouter/<int:dish_id>/",
        views.cart_add,
        name="cart_add",
    ),
    path(
        "panier/modifier/<int:dish_id>/",
        views.cart_update,
        name="cart_update",
    ),
    path(
        "panier/supprimer/<int:dish_id>/",
        views.cart_remove,
        name="cart_remove",
    ),
    path(
        "commander/",
        views.checkout,
        name="checkout",
    ),
    path(
        "commande/<int:order_id>/confirmation/",
        views.order_success,
        name="success",
    ),
    
    path(
        "livraison/tarif/",
        views.delivery_quote,
        name="delivery_quote",
    ),
]