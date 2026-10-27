from django.contrib import admin
from django.urls import include, path

from payments import views as payment_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", payment_views.home, name="home"),
    path("payments/", include("payments.urls")),
]
