"""
URLs de la app payments.
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Test Suite
    path('paytest/', views.test_index, name='test_index'),
    path('paytest/payment/', views.test_payment, name='test_payment'),
    path('paytest/customer/', views.test_customer, name='test_customer'),
    path('paytest/subscription/', views.test_subscription, name='test_subscription'),
    path('paytest/refund/', views.test_refund, name='test_refund'),

    # Webhooks y retorno
    path('confirm/', views.payment_confirm, name='payment_confirm'),
    path('return/', views.payment_return, name='payment_return'),
    path('customer/register-return/', views.customer_register_return, name='customer_register_return'),
    path('subscription/return/', views.subscription_return, name='subscription_return'),
]
