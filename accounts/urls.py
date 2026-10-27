from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.EmailLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("google/login/", views.google_login, name="google-login"),
    path(
        "google/callback/", views.google_callback, name="google-callback"
    ),
]
