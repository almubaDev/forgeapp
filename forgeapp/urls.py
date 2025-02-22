# forgeapp/urls.py (URLs de la aplicación)
from django.urls import path
from . import views

app_name = 'forgeapp'

urlpatterns = [
    # Landing
    path('', views.landing, name='landing'),
    path('contact/', views.contact_form, name='contact_form'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Applications URLs
    path('applications/', views.application_list, name='application_list'),
    path('applications/create/', views.application_create, name='application_create'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('applications/<int:pk>/update/', views.application_update, name='application_update'),
    path('applications/<int:pk>/delete/', views.application_delete, name='application_delete'),
    path('applications/<int:pk>/configs/', views.application_configs, name='application_configs'),
    path('applications/<int:pk>/configs/add/', views.application_config_add, name='application_config_add'),
    path('applications/configs/<int:config_pk>/edit/', views.application_config_edit, name='application_config_edit'),
    path('applications/configs/<int:config_pk>/delete/', views.application_config_delete, name='application_config_delete'),
    
    # Clients URLs
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/update/', views.client_update, name='client_update'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    
    # Subscriptions URLs
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/create/', views.subscription_create, name='subscription_create'),
    path('subscriptions/<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('subscriptions/<int:pk>/update/', views.subscription_update, name='subscription_update'),
    path('subscriptions/<int:pk>/delete/', views.subscription_delete, name='subscription_delete'),
    path('subscriptions/<int:pk>/activate/', views.subscription_activate, name='subscription_activate'),
    path('subscriptions/<int:pk>/suspend/', views.subscription_suspend, name='subscription_suspend'),
    path('subscriptions/<int:pk>/cancel/', views.subscription_cancel, name='subscription_cancel'),
    
    # Calculadora URLs
    path('calculadoras/', views.calculadora_list, name='calculadora_list'),
    path('calculadoras/create/', views.calculadora_create, name='calculadora_create'),
    path('calculadoras/<int:pk>/', views.calculadora_detail, name='calculadora_detail'),
    path('calculadoras/<int:pk>/update/', views.calculadora_update, name='calculadora_update'),
    path('calculadoras/<int:pk>/delete/', views.calculadora_delete, name='calculadora_delete'),
    path('calculadoras/<int:pk>/pdf/', views.calculadora_pdf, name='calculadora_pdf'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('calculadora/<int:pk>/generar-suscripciones/', views.generar_suscripciones, name='generar_suscripciones'),
]
