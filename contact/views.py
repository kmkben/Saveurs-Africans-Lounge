from django.shortcuts import render

# Create your views here.
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import ContactForm
from .models import ContactMessage


logger = logging.getLogger(__name__)


class ContactCreateView(CreateView):
    model = ContactMessage
    form_class = ContactForm
    template_name = "contact/contact.html"
    success_url = reverse_lazy("contact:success")

    def form_valid(self, form):
        response = super().form_valid(form)

        contact_message = self.object

        subject_label = contact_message.get_subject_display()

        email_subject = (
            f"[{settings.SITE_NAME}] "
            f"Nouveau message — {subject_label}"
        )

        email_body = self.build_email_body(contact_message)

        email = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
            reply_to=[contact_message.email],
        )

        try:
            email.send(fail_silently=False)
        except Exception:
            logger.exception(
                "Unable to send contact notification email "
                "for ContactMessage ID %s.",
                contact_message.pk,
            )

            messages.warning(
                self.request,
                (
                    "Votre message a bien été enregistré, "
                    "mais la notification par e-mail n’a pas pu "
                    "être envoyée immédiatement."
                ),
            )
        else:
            messages.success(
                self.request,
                "Votre message a bien été envoyé.",
            )

        return response

    @staticmethod
    def build_email_body(contact_message):
        phone = contact_message.phone or "Non renseigné"
        subject_detail = (
            contact_message.subject_detail
            or "Aucune précision"
        )

        return f"""
Nouveau message reçu depuis le site {settings.SITE_NAME}

Nom :
{contact_message.name}

Adresse e-mail :
{contact_message.email}

Téléphone :
{phone}

Sujet :
{contact_message.get_subject_display()}

Précision :
{subject_detail}

Message :
{contact_message.message}

Identifiant du message :
{contact_message.pk}
""".strip()


class ContactSuccessView(TemplateView):
    template_name = "contact/contact_success.html"