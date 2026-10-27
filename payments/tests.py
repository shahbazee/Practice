import hashlib
import hmac
import json
import time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Payment

User = get_user_model()


class PaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="testpass123",
        )

    def test_payment_list_requires_login(self):
        response = self.client.get(reverse("payment-list"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_sees_own_payments(self):
        Payment.objects.create(
            user=self.user,
            amount="25.00",
            currency="USD",
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("payment-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "25.00")


class StripeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="stripeuser",
            email="stripe@example.com",
            password="testpass123",
        )
        self.payment = Payment.objects.create(
            user=self.user,
            amount="10.00",
            currency="USD",
        )

    def test_checkout_requires_login(self):
        url = reverse("payment-checkout", args=[self.payment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_checkout_redirects_to_stripe_session(self):
        url = reverse("payment-checkout", args=[self.payment.id])
        self.client.force_login(self.user)
        with patch(
            "payments.services.stripe.checkout.Session.create"
        ) as mock_create:
            mock_create.return_value.id = "cs_test_123"
            mock_create.return_value.url = "https://checkout.test/x"
            response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://checkout.test/x")
        self.payment.refresh_from_db()
        self.assertEqual(
            self.payment.stripe_checkout_session_id, "cs_test_123"
        )

    def _signed_headers(self, payload, secret="whsec_test"):
        timestamp = str(int(time.time()))
        message = f"{timestamp}.{payload.decode('utf-8')}".encode()
        signature = hmac.new(
            secret.encode(), message, hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    def _post_webhook(self, event):
        payload = json.dumps(event).encode("utf-8")
        return self.client.post(
            reverse("stripe-webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=self._signed_headers(payload),
        )

    def _completed_event(self):
        return {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_intent": "pi_test_123",
                    "metadata": {
                        "user_id": str(self.user.id),
                        "payment_id": str(self.payment.id),
                    },
                }
            },
        }

    def test_webhook_bad_signature_returns_400(self):
        response = self.client.post(
            reverse("stripe-webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=bad",
        )
        self.assertEqual(response.status_code, 400)

    def test_webhook_completed_marks_payment_completed(self):
        with self.settings(STRIPE_WEBHOOK_SECRET="whsec_test"):
            response = self._post_webhook(self._completed_event())
        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.COMPLETED)
        self.assertEqual(
            self.payment.stripe_payment_intent_id, "pi_test_123"
        )

    def test_webhook_expired_marks_payment_failed(self):
        event = {
            "type": "checkout.session.expired",
            "data": {
                "object": {
                    "metadata": {
                        "user_id": str(self.user.id),
                        "payment_id": str(self.payment.id),
                    },
                }
            },
        }
        with self.settings(STRIPE_WEBHOOK_SECRET="whsec_test"):
            response = self._post_webhook(event)
        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.FAILED)
