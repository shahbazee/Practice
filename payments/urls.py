from django.urls import path

from . import views, webhooks
from .views import PaymentCreateView, PaymentListView

urlpatterns = [
    path("", PaymentListView.as_view(), name="payment-list"),
    path("new/", PaymentCreateView.as_view(), name="payment-new"),
    path(
        "<int:pk>/checkout/",
        views.CreateCheckoutSessionView.as_view(),
        name="payment-checkout",
    ),
    path(
        "success/",
        views.PaymentSuccessView.as_view(),
        name="payment-success",
    ),
    path(
        "cancel/",
        views.PaymentCancelView.as_view(),
        name="payment-cancel",
    ),
    path("webhook/stripe/", webhooks.stripe_webhook, name="stripe-webhook"),
]
