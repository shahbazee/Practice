from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string

User = get_user_model()


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")
    return render(request, "accounts/logout.html")


def google_login(request):
    state = get_random_string(32)
    request.session["google_oauth_state"] = state
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": request.build_absolute_uri(
            reverse("google-callback")
        ),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
        params
    )
    return redirect(url)


def google_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")
    saved_state = request.session.pop("google_oauth_state", None)
    if not code or not state or state != saved_state:
        return HttpResponseBadRequest("Invalid OAuth state.")
    try:
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": request.build_absolute_uri(
                    reverse("google-callback")
                ),
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        userinfo_response = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()
    except requests.RequestException:
        messages.error(request, "Google login failed. Try again.")
        return redirect("home")
    email = userinfo.get("email")
    if not email or not userinfo.get("email_verified", False):
        messages.error(request, "Google email not verified.")
        return redirect("home")
    user, created = User.objects.get_or_create(
        email=email, defaults={"username": email}
    )
    if created:
        user.first_name = userinfo.get("given_name", "")
        user.last_name = userinfo.get("family_name", "")
        user.set_unusable_password()
        user.save()
    login(request, user)
    return redirect("home")
