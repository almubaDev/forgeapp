from django.urls import path
from .views import (
    PaymentLinkListView,
    PaymentLinkCreateView,
    PaymentLinkDetailView,
    PaymentLinkUpdateView,
    PaymentLinkDeleteView,
    mercadopago_webhook,
    payment_return,
    check_payment_status,
    update_pending_payments,
    payment_result,
    verify_receipt,
    download_receipt,
    verify_code_form,
    verify_code_result,
)

app_name = 'checkout_counters'

urlpatterns = [
    path('', PaymentLinkListView.as_view(), name='payment_list'),
    path('create/', PaymentLinkCreateView.as_view(), name='payment_create'),
    path('webhook/mercadopago/', mercadopago_webhook, name='mercadopago_webhook'),
    path('payment/return/', payment_return, name='payment_return'),
    path('payment/result/<str:reference_id>/', payment_result, name='payment_result'),
    path('update-pending/', update_pending_payments, name='update_pending_payments'),
    
    # URLs para detalle de pago (soporta pk y reference_id)
    path('payment/<int:pk>/', PaymentLinkDetailView.as_view(), name='payment_detail'),
    path('payment/ref/<str:reference_id>/', PaymentLinkDetailView.as_view(), name='payment_detail_by_ref'),
    
    # URLs para actualización y eliminación
    path('payment/<int:pk>/update/', PaymentLinkUpdateView.as_view(), name='payment_update'),
    path('payment/<int:pk>/delete/', PaymentLinkDeleteView.as_view(), name='payment_delete'),
    
    # URL para verificación de estado
    path('payment/<str:reference_id>/check/', check_payment_status, name='check_payment_status'),
    
    # URLs para verificación de comprobante
    path('receipt/verify/<uuid:secret_code>/', verify_receipt, name='verify_receipt'),
    path('receipt/verify/', verify_code_form, name='verify_code_form'),
    path('receipt/verify/code/<str:verification_code>/', verify_code_result, name='verify_code_result'),
    
    # URL para descarga de comprobante
    path('receipt/download/<str:receipt_number>/', download_receipt, name='download_receipt'),
]
