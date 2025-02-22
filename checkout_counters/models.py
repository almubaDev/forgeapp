# checkout_counters/models.py
from django.db import models
from django.urls import reverse

class PaymentLink(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('expired', 'Expirado'),
        ('cancelled', 'Cancelado')
    ]
    reference_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    payment_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_paid = models.BooleanField(default=False)
    payer_email = models.EmailField(blank=True, null=True)
    payer_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.description} - ${self.amount} - {self.get_status_display()}"

    def get_absolute_url(self):
        return reverse('checkout_counters:payment_detail', args=[str(self.id)])