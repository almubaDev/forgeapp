from django.urls import path
from .views import (
    PaymentLinkListView,
    PaymentLinkCreateView,
    PaymentLinkDetailView,
    PaymentLinkUpdateView,
)

app_name = 'checkout_counters'

urlpatterns = [
    path('', PaymentLinkListView.as_view(), name='payment_list'),
    path('create/', PaymentLinkCreateView.as_view(), name='payment_create'),
    path('<int:pk>/', PaymentLinkDetailView.as_view(), name='payment_detail'),
    path('<int:pk>/update/', PaymentLinkUpdateView.as_view(), name='payment_update'),
]