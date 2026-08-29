import logging

import requests

from django.conf import settings
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_SMS_URL = "https://api.brevo.com/v3/transactionalSMS/send"


# ==================================================
# LOW LEVEL EMAIL
# ==================================================

def send_email(
    *,
    to_email,
    subject,
    html_content,
    to_name="",
):
    """
    Send a transactional email through Brevo.
    """

    if not settings.BREVO_EMAIL_ENABLED:
        logger.info(
            "Brevo email disabled. Email not sent to %s.",
            to_email,
        )
        return None

    if not settings.BREVO_API_KEY:
        raise RuntimeError(
            "BREVO_API_KEY is not configured."
        )

    if not settings.BREVO_SENDER_EMAIL:
        raise RuntimeError(
            "BREVO_SENDER_EMAIL is not configured."
        )

    if not to_email:
        logger.warning(
            "Email recipient is empty."
        )
        return None

    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL,
        },
        "to": [
            {
                "email": to_email,
                "name": to_name,
            }
        ],
        "subject": subject,
        "htmlContent": html_content,
    }

    response = requests.post(
        BREVO_EMAIL_URL,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": settings.BREVO_API_KEY,
        },
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# ==================================================
# LOW LEVEL SMS
# ==================================================

def send_sms(
    *,
    phone,
    content,
):
    """
    Send a transactional SMS through Brevo.
    """

    if not settings.BREVO_SMS_ENABLED:
        logger.info(
            "Brevo SMS disabled. SMS not sent to %s.",
            phone,
        )
        return None

    if not settings.BREVO_API_KEY:
        raise RuntimeError(
            "BREVO_API_KEY is not configured."
        )

    if not settings.BREVO_SMS_SENDER:
        raise RuntimeError(
            "BREVO_SMS_SENDER is not configured."
        )

    if not phone:
        logger.warning(
            "SMS recipient phone number is empty."
        )
        return None

    payload = {
        "sender": settings.BREVO_SMS_SENDER,
        "recipient": str(phone),
        "content": content,
        "type": "transactional",
    }

    response = requests.post(
        BREVO_SMS_URL,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": settings.BREVO_API_KEY,
        },
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# ==================================================
# ORDER NOTIFICATIONS
# ==================================================

def send_order_paid_notifications(order):
    """
    Send notifications for a paid order.

    Email:
    - customer
    - restaurant owner / kitchen

    SMS:
    - customer
    - restaurant owner / kitchen

    Email and SMS are tracked independently to prevent
    duplicate notifications.
    """

    # ==================================================
    # EMAIL NOTIFICATIONS
    # ==================================================

    if (
        not order.email_notifications_sent
        and settings.BREVO_EMAIL_ENABLED
    ):
        customer_html = render_to_string(
            "notifications/emails/order_customer.html",
            {
                "order": order,
            },
        )

        owner_html = render_to_string(
            "notifications/emails/order_owner.html",
            {
                "order": order,
            },
        )

        # Customer
        if order.email:
            send_email(
                to_email=order.email,
                to_name=order.customer_name,
                subject=(
                    f"Commande #{order.pk} confirmée "
                    f"| {settings.BREVO_SENDER_NAME}"
                ),
                html_content=customer_html,
            )

        # Owner / kitchen
        if settings.OWNER_NOTIFICATION_EMAIL:
            send_email(
                to_email=settings.OWNER_NOTIFICATION_EMAIL,
                to_name="Saveurs Africans Lounge",
                subject=(
                    f"Nouvelle commande payée #{order.pk}"
                ),
                html_content=owner_html,
            )

        order.email_notifications_sent = True

        order.save(
            update_fields=[
                "email_notifications_sent",
            ]
        )

        logger.info(
            "Order #%s email notifications sent.",
            order.pk,
        )

    # ==================================================
    # SMS NOTIFICATIONS
    # ==================================================

    if (
        not order.sms_notifications_sent
        and settings.BREVO_SMS_ENABLED
    ):
        # Customer
        if order.phone:
            send_sms(
                phone=order.phone,
                content=(
                    f"Saveurs Africans Lounge : "
                    f"commande #{order.pk} confirmee. "
                    f"Paiement de {order.total:.2f} EUR recu. "
                    f"Merci pour votre commande."
                ),
            )

        # Owner / kitchen
        if settings.OWNER_NOTIFICATION_PHONE:
            send_sms(
                phone=settings.OWNER_NOTIFICATION_PHONE,
                content=(
                    f"Nouvelle commande #{order.pk} payee - "
                    f"{order.get_order_type_display()} - "
                    f"{order.total:.2f} EUR. "
                    f"Client : {order.customer_name}. "
                    f"A preparer."
                ),
            )

        order.sms_notifications_sent = True

        order.save(
            update_fields=[
                "sms_notifications_sent",
            ]
        )

        logger.info(
            "Order #%s SMS notifications sent.",
            order.pk,
        )


# ==================================================
# RESERVATION NOTIFICATIONS
# ==================================================

def send_reservation_paid_notifications(reservation):
    """
    Send notifications for a paid reservation.

    Email:
    - customer
    - restaurant owner

    SMS:
    - customer
    - restaurant owner

    Email and SMS are tracked independently to prevent
    duplicate notifications.
    """

    # ==================================================
    # EMAIL NOTIFICATIONS
    # ==================================================

    if (
        not reservation.email_notifications_sent
        and settings.BREVO_EMAIL_ENABLED
    ):
        customer_html = render_to_string(
            "notifications/emails/reservation_customer.html",
            {
                "reservation": reservation,
            },
        )

        owner_html = render_to_string(
            "notifications/emails/reservation_owner.html",
            {
                "reservation": reservation,
            },
        )

        # Customer
        if reservation.email:
            send_email(
                to_email=reservation.email,
                to_name=reservation.full_name,
                subject=(
                    "Votre réservation est enregistrée "
                    f"| {settings.BREVO_SENDER_NAME}"
                ),
                html_content=customer_html,
            )

        # Owner
        if settings.OWNER_NOTIFICATION_EMAIL:
            send_email(
                to_email=settings.OWNER_NOTIFICATION_EMAIL,
                to_name="Saveurs Africans Lounge",
                subject=(
                    "Nouvelle réservation payée "
                    f"#{reservation.pk}"
                ),
                html_content=owner_html,
            )

        reservation.email_notifications_sent = True

        reservation.save(
            update_fields=[
                "email_notifications_sent",
            ]
        )

        logger.info(
            "Reservation #%s email notifications sent.",
            reservation.pk,
        )

    # ==================================================
    # SMS NOTIFICATIONS
    # ==================================================

    if (
        not reservation.sms_notifications_sent
        and settings.BREVO_SMS_ENABLED
    ):
        # Customer
        if reservation.phone:
            send_sms(
                phone=reservation.phone,
                content=(
                    f"Saveurs Africans Lounge : "
                    f"reservation confirmee pour "
                    f"{reservation.number_of_guests} personne(s), "
                    f"le {reservation.reservation_date:%d/%m/%Y} "
                    f"a {reservation.reservation_time:%H:%M}. "
                    f"Acompte de "
                    f"{reservation.deposit_amount:.2f} EUR recu."
                ),
            )

        # Owner
        if settings.OWNER_NOTIFICATION_PHONE:
            send_sms(
                phone=settings.OWNER_NOTIFICATION_PHONE,
                content=(
                    f"Nouvelle reservation #{reservation.pk} payee - "
                    f"{reservation.get_reservation_type_display()} - "
                    f"{reservation.number_of_guests} pers. - "
                    f"{reservation.reservation_date:%d/%m/%Y} "
                    f"a {reservation.reservation_time:%H:%M}. "
                    f"Client : {reservation.full_name}."
                ),
            )

        reservation.sms_notifications_sent = True

        reservation.save(
            update_fields=[
                "sms_notifications_sent",
            ]
        )

        logger.info(
            "Reservation #%s SMS notifications sent.",
            reservation.pk,
        )