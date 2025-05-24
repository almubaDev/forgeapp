from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Dashboard y reportes generales
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/monthly/', views.monthly_report, name='monthly_report'),
    path('reports/annual/', views.annual_report, name='annual_report'),
    path('reports/cash-flow/', views.cash_flow_report, name='cash_flow_report'),
    
    # Pagos
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/mark-completed/', views.payment_mark_completed, name='payment_mark_completed'),
    path('payments/<int:pk>/generate-receipt/', views.payment_generate_receipt, name='payment_generate_receipt'),
    path('subscriptions/<int:subscription_id>/register-payment/', 
         views.register_subscription_payment, 
         name='register_subscription_payment'),
    
    # Recibos
    path('receipts/<int:pk>/download/', views.receipt_download, name='receipt_download'),
    path('receipts/<int:pk>/send/', views.receipt_send, name='receipt_send'),
         
    # Transacciones
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/summary/', views.transaction_summary, name='transaction_summary'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<int:pk>/update/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
]
