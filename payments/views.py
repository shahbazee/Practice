from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .models import Payment


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
