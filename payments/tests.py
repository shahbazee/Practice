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
