import stripe
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from .models import Payment
from .services import create_stripe_checkout_session


def home(request):
    return render(request, "home.html")


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = "payments/payment_list.html"

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    fields = ["amount", "currency"]
    template_name = "payments/payment_form.html"
    success_url = reverse_lazy("payment-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CreateCheckoutSessionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        payment = get_object_or_404(
            Payment, pk=pk, user=request.user
        )
        if payment.status != Payment.Status.PENDING:
            messages.error(request, "Only pending payments can be paid.")
            return redirect("payment-list")
        success_url = request.build_absolute_uri(
            reverse("payment-success")
        ) + f"?payment_id={payment.id}"
        cancel_url = request.build_absolute_uri(
            reverse("payment-cancel")
        ) + f"?payment_id={payment.id}"
        try:
            session = create_stripe_checkout_session(
                payment, success_url, cancel_url
            )
        except stripe.error.StripeError:
            messages.error(
                request, "Stripe could not start checkout. Try again."
            )
            return redirect("payment-list")
        return redirect(session.url)


class PaymentResultView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = self.request.GET.get("payment_id")
        payment = None
        if payment_id:
            payment = Payment.objects.filter(
                pk=payment_id, user=self.request.user
            ).first()
        context["payment"] = payment
        return context


class PaymentSuccessView(PaymentResultView):
    template_name = "payments/payment_success.html"


class PaymentCancelView(PaymentResultView):
    template_name = "payments/payment_cancel.html"
