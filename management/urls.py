from django.urls import path

from . import views


app_name = "management"


urlpatterns = [
    
    # ======================================================
    # Authentication
    # ======================================================

    path("connexion/", views.management_login, name="login"),
    path("deconnexion/", views.management_logout, name="logout"),


    # ==================================================
    # DASHBOARD
    # ==================================================

    path("", views.dashboard, name="dashboard"),


    # ==================================================
    # ORDERS
    # ==================================================

    path("commandes/", views.orders_list, name="orders_list"),
    path("commandes/<int:order_id>/", views.order_detail, name="order_detail"),
    path("commandes/<int:order_id>/statut/", views.order_status_update, name="order_status_update"),


    # ==================================================
    # RESERVATIONS
    # ==================================================

    path("reservations/", views.reservations_list, name="reservations_list"),
    path("reservations/<int:reservation_id>/", views.reservation_detail, name="reservation_detail"),
    path("reservations/<int:reservation_id>/statut/", views.reservation_status_update, name="reservation_status_update"),


    # ==================================================
    # MENU - DISHES
    # ==================================================

    path("carte/", views.dishes_list, name="dishes_list"),
    path("carte/ajouter/", views.dish_create, name="dish_create"),
    path("carte/<int:dish_id>/modifier/", views.dish_update, name="dish_update"),

    path(
        "carte/<int:dish_id>/supprimer/",
        views.dish_delete,
        name="dish_delete",
    ),

    path(
        "carte/<int:dish_id>/disponibilite/",
        views.dish_toggle_availability,
        name="dish_toggle_availability",
    ),


    # ==================================================
    # MENU CATEGORIES
    # ==================================================

    path(
        "categories/",
        views.categories_list,
        name="categories_list",
    ),

    path(
        "categories/ajouter/",
        views.category_create,
        name="category_create",
    ),

    path(
        "categories/<int:category_id>/modifier/",
        views.category_update,
        name="category_update",
    ),

    path(
        "categories/<int:category_id>/supprimer/",
        views.category_delete,
        name="category_delete",
    ),


    # ==================================================
    # ALLERGENS
    # ==================================================

    path(
        "allergenes/",
        views.allergens_list,
        name="allergens_list",
    ),

    path(
        "allergenes/ajouter/",
        views.allergen_create,
        name="allergen_create",
    ),

    path(
        "allergenes/<int:allergen_id>/modifier/",
        views.allergen_update,
        name="allergen_update",
    ),

    path(
        "allergenes/<int:allergen_id>/supprimer/",
        views.allergen_delete,
        name="allergen_delete",
    ),


    # ==================================================
    # DAILY SPECIALS
    # ==================================================

    path("plats-du-jour/",views.daily_specials_list, name="daily_specials_list"),
    path("plats-du-jour/ajouter/", views.daily_special_create, name="daily_special_create"),
    path("plats-du-jour/<int:special_id>/modifier/", views.daily_special_update, name="daily_special_update"),
    path("plats-du-jour/<int:special_id>/supprimer/", views.daily_special_delete, name="daily_special_delete"),
    path("plats-du-jour/<int:special_id>/publication/", views.daily_special_toggle_published, name="daily_special_toggle_published"),
    
    
    
    # ==================================================
    # PROMOTIONS 
    # ==================================================

    path("promotions/", views.manage_promotions_list, name="promotions_list"),
    path("promotions/create/", views.manage_promotion_create, name="promotion_create"),
    path("promotions/<int:pk>/edit/", views.manage_promotion_update, name="promotion_update"),
    path("promotions/<int:pk>/toggle/", views.manage_promotion_toggle, name="promotion_toggle"),

    

    # ==================================================
    # EVENTS
    # ==================================================

    path(
        "evenements/",
        views.events_list,
        name="events_list",
    ),

    path(
        "evenements/ajouter/",
        views.event_create,
        name="event_create",
    ),

    path(
        "evenements/<int:event_id>/modifier/",
        views.event_update,
        name="event_update",
    ),

    path(
        "evenements/<int:event_id>/supprimer/",
        views.event_delete,
        name="event_delete",
    ),

    path(
        "evenements/<int:event_id>/publication/",
        views.event_toggle_published,
        name="event_toggle_published",
    ),


    # ==================================================
    # GALLERY - ALBUMS
    # ==================================================

    path(
        "galerie/",
        views.gallery_albums_list,
        name="gallery_albums_list",
    ),

    path(
        "galerie/ajouter/",
        views.gallery_album_create,
        name="gallery_album_create",
    ),

    path(
        "galerie/<int:album_id>/",
        views.gallery_album_detail,
        name="gallery_album_detail",
    ),

    path(
        "galerie/<int:album_id>/modifier/",
        views.gallery_album_update,
        name="gallery_album_update",
    ),

    path(
        "galerie/<int:album_id>/supprimer/",
        views.gallery_album_delete,
        name="gallery_album_delete",
    ),


    # ==================================================
    # GALLERY - IMAGES
    # ==================================================

    path(
        "galerie/<int:album_id>/images/ajouter/",
        views.gallery_image_create,
        name="gallery_image_create",
    ),

    path(
        "galerie/images/<int:image_id>/modifier/",
        views.gallery_image_update,
        name="gallery_image_update",
    ),

    path(
        "galerie/images/<int:image_id>/supprimer/",
        views.gallery_image_delete,
        name="gallery_image_delete",
    ),


    # ==================================================
    # CONTACT MESSAGES
    # ==================================================

    path(
        "messages/",
        views.messages_list,
        name="messages_list",
    ),

    path(
        "messages/<int:message_id>/",
        views.message_detail,
        name="message_detail",
    ),

    path(
        "messages/<int:message_id>/lecture/",
        views.message_toggle_read,
        name="message_toggle_read",
    ),

    path(
        "messages/<int:message_id>/supprimer/",
        views.message_delete,
        name="message_delete",
    ),


    # ==================================================
    # DELIVERY ZONES
    # ==================================================

    path(
        "zones-livraison/",
        views.delivery_zones_list,
        name="delivery_zones_list",
    ),

    path(
        "zones-livraison/ajouter/",
        views.delivery_zone_create,
        name="delivery_zone_create",
    ),

    path(
        "zones-livraison/<int:zone_id>/modifier/",
        views.delivery_zone_update,
        name="delivery_zone_update",
    ),

    path(
        "zones-livraison/<int:zone_id>/supprimer/",
        views.delivery_zone_delete,
        name="delivery_zone_delete",
    ),

    path(
        "zones-livraison/<int:zone_id>/activation/",
        views.delivery_zone_toggle_active,
        name="delivery_zone_toggle_active",
    ),


    # ==================================================
    # SITE SETTINGS
    # ==================================================

    path(
        "parametres/",
        views.site_settings,
        name="site_settings",
    ),
]