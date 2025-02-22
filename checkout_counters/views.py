# checkout_counters/views.py
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .models import PaymentLink
import uuid
from datetime import datetime, timedelta

class PaymentLinkListView(LoginRequiredMixin, ListView):
    model = PaymentLink
    template_name = 'checkout_counters/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_amount'] = sum(payment.amount for payment in self.get_queryset().filter(status='paid'))
        context['pending_amount'] = sum(payment.amount for payment in self.get_queryset().filter(status='pending'))
        return context

class PaymentLinkCreateView(LoginRequiredMixin, CreateView):
    model = PaymentLink
    fields = ['amount', 'description']
    template_name = 'checkout_counters/payment_form.html'
    success_url = reverse_lazy('checkout_counters:payment_list')

    def form_valid(self, form):
        form.instance.reference_id = str(uuid.uuid4())
        form.instance.expires_at = datetime.now() + timedelta(days=7)
        # Aquí iría la lógica para generar el link de pago de Mercado Pago
        form.instance.payment_link = f"https://mpago.la/{form.instance.reference_id[:8]}"
        messages.success(self.request, 'Link de pago creado exitosamente')
        return super().form_valid(form)

class PaymentLinkDetailView(LoginRequiredMixin, DetailView):
    model = PaymentLink
    template_name = 'checkout_counters/payment_detail.html'
    context_object_name = 'payment'

class PaymentLinkUpdateView(LoginRequiredMixin, UpdateView):
    model = PaymentLink
    fields = ['status', 'payer_email', 'payer_name']
    template_name = 'checkout_counters/payment_form.html'