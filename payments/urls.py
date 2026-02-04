"""
URLs de la app payments.
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Test Suite Principal (selector de proveedores)
    path('paytest/', views.test_index, name='test_index'),

    # Flow Test Suite
    path('paytest/flow/', views.flow_test_index, name='flow_test_index'),
    path('paytest/flow/payment/', views.flow_test_payment, name='flow_test_payment'),
    path('paytest/flow/customer/', views.flow_test_customer, name='flow_test_customer'),
    path('paytest/flow/subscription/', views.flow_test_subscription, name='flow_test_subscription'),
    path('paytest/flow/refund/', views.flow_test_refund, name='flow_test_refund'),

    # Flow Webhooks y retorno
    path('confirm/', views.payment_confirm, name='payment_confirm'),
    path('return/', views.payment_return, name='payment_return'),
    path('customer/register-return/', views.customer_register_return, name='customer_register_return'),
    path('subscription/return/', views.subscription_return, name='subscription_return'),
]
