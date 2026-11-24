from datetime import date, time
from decimal import Decimal
from unittest.mock import Mock, patch

import stripe

from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order
from reservations.models import Reservation
from payments.services import euros_to_cents
from payments.views import (
    _get_or_create_checkout,
    _mark_order_paid,
    _mark_reservation_paid,
)


class PaymentTestMixin:
    def make_order(self):
        return Order.objects.create(
            customer_name="Test Customer",
            email="customer@example.com",
            phone="0600000000",
            delivery_fee=Decimal("12.50"),
            payment_method="STRIPE",
            payment_reference="cs_test_order_123",
        )

    def make_reservation(self):
        return Reservation.objects.create(
            first_name="Test",
            last_name="Customer",
            email="customer@example.com",
            phone="0600000000",
            reservation_date=date(2026, 12, 15),
            reservation_time=time(19, 30),
            number_of_guests=2,
            deposit_amount=Decimal("20.00"),
            deposit_reference="cs_test_reservation_123",
        )

    def make_session(
        self,
        *,
        session_id,
        payment_type,
        object_id,
        amount,
        currency="eur",
        status="complete",
        payment_status="paid",
    ):
        identifier = (
            "order_id" if payment_type == "order" else "reservation_id"
        )
        return {
            "id": session_id,
            "mode": "payment",
            "status": status,
            "payment_status": payment_status,
            "currency": currency,
            "amount_total": euros_to_cents(amount),
            "metadata": {
                "payment_type": payment_type,
                identifier: str(object_id),
            },
        }


class MoneyConversionTests(TestCase):
    def test_euros_to_cents(self):
        self.assertEqual(euros_to_cents(Decimal("12.50")), 1250)
        self.assertEqual(euros_to_cents(Decimal("9.99")), 999)

    def test_invalid_amounts(self):
        for amount in (Decimal("0"), Decimal("-5"), "invalid", float("nan")):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    euros_to_cents(amount)


class OrderPaymentTests(PaymentTestMixin, TestCase):
    @patch("payments.views._notify_order")
    def test_valid_order_payment(self, notify):
        order = self.make_order()
        session = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=order.total,
        )
        with self.captureOnCommitCallbacks(execute=True):
            result = _mark_order_paid(session)
        order.refresh_from_db()
        self.assertTrue(result)
        self.assertTrue(order.is_paid)
        self.assertEqual(order.amount_paid, Decimal("12.50"))
        self.assertIsNotNone(order.paid_at)
        notify.assert_called_once_with(order.pk)

    @patch("payments.views._notify_order")
    def test_duplicate_webhook(self, notify):
        order = self.make_order()
        session = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=order.total,
        )
        with self.captureOnCommitCallbacks(execute=True):
            first = _mark_order_paid(session)
            second = _mark_order_paid(session)
        self.assertTrue(first)
        self.assertTrue(second)
        notify.assert_called_once()

    @patch("payments.views._notify_order")
    def test_wrong_amount_rejected(self, notify):
        order = self.make_order()
        session = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=Decimal("1.00"),
        )
        result = _mark_order_paid(session)
        order.refresh_from_db()
        self.assertFalse(result)
        self.assertFalse(order.is_paid)
        notify.assert_not_called()

    @patch("payments.views._notify_order")
    def test_wrong_currency_rejected(self, notify):
        order = self.make_order()
        session = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=order.total,
            currency="usd",
        )
        result = _mark_order_paid(session)
        order.refresh_from_db()
        self.assertFalse(result)
        self.assertFalse(order.is_paid)
        notify.assert_not_called()

    def test_unauthorized_order_payment(self):
        order = self.make_order()
        response = self.client.post(reverse("payments:order", args=[order.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("orders:cart"))


class ReservationPaymentTests(PaymentTestMixin, TestCase):
    @patch("payments.views._notify_reservation")
    def test_valid_reservation_payment(self, notify):
        reservation = self.make_reservation()
        session = self.make_session(
            session_id=reservation.deposit_reference,
            payment_type="reservation",
            object_id=reservation.pk,
            amount=reservation.deposit_amount,
        )
        with self.captureOnCommitCallbacks(execute=True):
            result = _mark_reservation_paid(session)
        reservation.refresh_from_db()
        self.assertTrue(result)
        self.assertTrue(reservation.deposit_is_paid)
        self.assertIsNotNone(reservation.deposit_paid_at)
        notify.assert_called_once_with(reservation.pk)

    @patch("payments.views._notify_reservation")
    def test_duplicate_reservation_webhook(self, notify):
        reservation = self.make_reservation()
        session = self.make_session(
            session_id=reservation.deposit_reference,
            payment_type="reservation",
            object_id=reservation.pk,
            amount=reservation.deposit_amount,
        )
        with self.captureOnCommitCallbacks(execute=True):
            first = _mark_reservation_paid(session)
            second = _mark_reservation_paid(session)
        self.assertTrue(first)
        self.assertTrue(second)
        notify.assert_called_once()

    def test_unauthorized_reservation_payment(self):
        reservation = self.make_reservation()
        response = self.client.post(
            reverse("payments:reservation", args=[reservation.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("reservations:create"))


class CheckoutLifecycleTests(PaymentTestMixin, TestCase):
    @patch("payments.views.retrieve_checkout_session")
    @patch("payments.views.create_order_checkout_session")
    def test_existing_open_session_is_reused(self, create_session, retrieve_session):
        order = self.make_order()
        existing = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=order.total,
            status="open",
            payment_status="unpaid",
        )
        existing["url"] = "https://checkout.stripe.com/test"
        retrieve_session.return_value = existing
        session = _get_or_create_checkout(
            Mock(),
            model=Order,
            pk=order.pk,
            reference_field="payment_reference",
            paid_field=lambda obj: obj.is_paid,
            payment_type="order",
            amount_field=lambda obj: obj.total,
            create_session=create_session,
        )
        self.assertEqual(session["id"], order.payment_reference)
        create_session.assert_not_called()

    @patch("payments.views.retrieve_checkout_session")
    @patch("payments.views.create_order_checkout_session")
    def test_paid_session_is_not_replaced(self, create_session, retrieve_session):
        order = self.make_order()
        existing = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=order.total,
        )
        retrieve_session.return_value = existing
        with self.assertRaises(ValueError):
            _get_or_create_checkout(
                Mock(),
                model=Order,
                pk=order.pk,
                reference_field="payment_reference",
                paid_field=lambda obj: obj.is_paid,
                payment_type="order",
                amount_field=lambda obj: obj.total,
                create_session=create_session,
            )
        create_session.assert_not_called()

    @patch("payments.views.retrieve_checkout_session")
    def test_stripe_retrieval_error_does_not_replace_session(self, retrieve_session):
        order = self.make_order()
        retrieve_session.side_effect = stripe.APIConnectionError(
            message="Stripe unavailable"
        )
        with self.assertRaises(stripe.StripeError):
            _get_or_create_checkout(
                Mock(),
                model=Order,
                pk=order.pk,
                reference_field="payment_reference",
                paid_field=lambda obj: obj.is_paid,
                payment_type="order",
                amount_field=lambda obj: obj.total,
                create_session=Mock(),
            )


@override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_secret")
class StripeWebhookTests(PaymentTestMixin, TestCase):
    @patch("payments.views.stripe.Webhook.construct_event")
    @patch("payments.views._notify_order")
    def test_valid_order_webhook(self, notify, construct_event):
        order = self.make_order()
        session = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=order.total,
        )
        construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": session},
        }
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("payments:stripe_webhook"),
                data=b"{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test_signature",
            )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertTrue(order.is_paid)
        notify.assert_called_once_with(order.pk)

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_invalid_signature_rejected(self, construct_event):
        construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "bad_signature"
        )
        response = self.client.post(
            reverse("payments:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="bad_signature",
        )
        self.assertEqual(response.status_code, 400)

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_wrong_amount_webhook_rejected(self, construct_event):
        order = self.make_order()
        session = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=Decimal("1.00"),
        )
        construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": session},
        }
        response = self.client.post(
            reverse("payments:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test_signature",
        )
        self.assertEqual(response.status_code, 409)
        order.refresh_from_db()
        self.assertFalse(order.is_paid)


class PaymentSuccessRedirectTests(PaymentTestMixin, TestCase):
    def authorize_order(self, order):
        session = self.client.session
        session["pending_order_id"] = order.pk
        session.save()

    def authorize_reservation(self, reservation):
        session = self.client.session
        session["last_reservation_id"] = reservation.pk
        session.save()

    @patch("payments.views._notify_reservation")
    @patch("payments.views.retrieve_checkout_session")
    def test_reservation_success_confirms_paid_session(self, retrieve_session, notify):
        reservation = self.make_reservation()
        self.authorize_reservation(reservation)
        retrieve_session.return_value = self.make_session(
            session_id=reservation.deposit_reference,
            payment_type="reservation",
            object_id=reservation.pk,
            amount=reservation.deposit_amount,
        )
        url = reverse("payments:reservation_success", args=[reservation.pk])
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(
                url, {"session_id": reservation.deposit_reference}
            )
        reservation.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("reservations:success"))
        self.assertTrue(reservation.deposit_is_paid)
        self.assertIsNotNone(reservation.deposit_paid_at)
        notify.assert_called_once_with(reservation.pk)

    @patch("payments.views._notify_order")
    @patch("payments.views.retrieve_checkout_session")
    def test_order_success_confirms_paid_session(self, retrieve_session, notify):
        order = self.make_order()
        self.authorize_order(order)
        retrieve_session.return_value = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=order.total,
        )
        url = reverse("payments:order_success", args=[order.pk])
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(url, {"session_id": order.payment_reference})
        order.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("orders:success", args=[order.pk]),
        )
        self.assertTrue(order.is_paid)
        self.assertEqual(order.amount_paid, order.total)
        notify.assert_called_once_with(order.pk)

    @patch("payments.views._notify_reservation")
    @patch("payments.views.retrieve_checkout_session")
    def test_unpaid_reservation_is_not_confirmed(self, retrieve_session, notify):
        reservation = self.make_reservation()
        self.authorize_reservation(reservation)
        retrieve_session.return_value = self.make_session(
            session_id=reservation.deposit_reference,
            payment_type="reservation",
            object_id=reservation.pk,
            amount=reservation.deposit_amount,
            status="open",
            payment_status="unpaid",
        )
        response = self.client.get(
            reverse("payments:reservation_success", args=[reservation.pk]),
            {"session_id": reservation.deposit_reference},
        )
        reservation.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("reservations:deposit", args=[reservation.pk]),
        )
        self.assertFalse(reservation.deposit_is_paid)
        notify.assert_not_called()

    @patch("payments.views._notify_order")
    @patch("payments.views.retrieve_checkout_session")
    def test_wrong_amount_order_is_not_confirmed(self, retrieve_session, notify):
        order = self.make_order()
        self.authorize_order(order)
        retrieve_session.return_value = self.make_session(
            session_id=order.payment_reference,
            payment_type="order",
            object_id=order.pk,
            amount=Decimal("1.00"),
        )
        response = self.client.get(
            reverse("payments:order_success", args=[order.pk]),
            {"session_id": order.payment_reference},
        )
        order.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("orders:payment", args=[order.pk]),
        )
        self.assertFalse(order.is_paid)
        notify.assert_not_called()

    @patch("payments.views._notify_reservation")
    @patch("payments.views.retrieve_checkout_session")
    def test_duplicate_reservation_confirmation(self, retrieve_session, notify):
        reservation = self.make_reservation()
        self.authorize_reservation(reservation)
        retrieve_session.return_value = self.make_session(
            session_id=reservation.deposit_reference,
            payment_type="reservation",
            object_id=reservation.pk,
            amount=reservation.deposit_amount,
        )
        url = reverse("payments:reservation_success", args=[reservation.pk])
        with self.captureOnCommitCallbacks(execute=True):
            first = self.client.get(
                url, {"session_id": reservation.deposit_reference}
            )
            second = self.client.get(
                url, {"session_id": reservation.deposit_reference}
            )
        reservation.refresh_from_db()
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertTrue(reservation.deposit_is_paid)
        retrieve_session.assert_called_once()
        notify.assert_called_once_with(reservation.pk)

    @patch("payments.views.retrieve_checkout_session")
    def test_unauthorized_reservation_success(self, retrieve_session):
        reservation = self.make_reservation()
        response = self.client.get(
            reverse("payments:reservation_success", args=[reservation.pk]),
            {"session_id": reservation.deposit_reference},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("reservations:create"))
        retrieve_session.assert_not_called()

    @patch("payments.views.retrieve_checkout_session")
    def test_untrusted_session_id_is_rejected(self, retrieve_session):
        reservation = self.make_reservation()
        self.authorize_reservation(reservation)
        response = self.client.get(
            reverse("payments:reservation_success", args=[reservation.pk]),
            {"session_id": "cs_test_untrusted"},
        )
        reservation.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(reservation.deposit_is_paid)
        retrieve_session.assert_not_called()
