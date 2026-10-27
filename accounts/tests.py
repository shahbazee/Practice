from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class GoogleOAuthTests(TestCase):
    def test_google_login_redirects_to_google(self):
        response = self.client.get(reverse("google-login"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response.url)
        self.assertIn("client_id", response.url)
        state = self.client.session["google_oauth_state"]
        self.assertIn("state", response.url)
        self.assertTrue(state)

    def test_callback_state_mismatch_returns_400(self):
        session = self.client.session
        session["google_oauth_state"] = "correct-state"
        session.save()
        url = reverse("google-callback") + "?code=x&state=wrong-state"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def _mock_google(self, mock_post, mock_get):
        mock_post.return_value.json.return_value = {
            "access_token": "token123"
        }
        mock_get.return_value.json.return_value = {
            "email": "google@example.com",
            "email_verified": True,
            "given_name": "Google",
            "family_name": "User",
        }

    def _callback_url(self):
        session = self.client.session
        session["google_oauth_state"] = "test-state"
        session.save()
        return reverse("google-callback") + "?code=abc&state=test-state"

    def test_callback_creates_and_logs_in_user(self):
        url = self._callback_url()
        with patch("accounts.views.requests.post") as mock_post, patch(
            "accounts.views.requests.get"
        ) as mock_get:
            self._mock_google(mock_post, mock_get)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        user = User.objects.get(email="google@example.com")
        self.assertEqual(user.first_name, "Google")
        self.assertIn("_auth_user_id", self.client.session)

    def test_callback_reuses_existing_user(self):
        User.objects.create_user(
            username="google@example.com", email="google@example.com"
        )
        url = self._callback_url()
        with patch("accounts.views.requests.post") as mock_post, patch(
            "accounts.views.requests.get"
        ) as mock_get:
            self._mock_google(mock_post, mock_get)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), 1)

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
