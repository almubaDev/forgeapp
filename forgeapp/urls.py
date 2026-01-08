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
    path('clients/<int:pk>/payment-history/', views.client_payment_history, name='client_payment_history'),
    path('clients/<int:pk>/contracts/', views.client_contracts, name='client_contracts'),
    path('clients/<int:pk>/contracts/<int:token_id>/', views.view_client_contract, name='view_client_contract'),
    path('clients/<int:pk>/contracts/<int:token_id>/delete/', views.delete_contract, name='delete_contract'),
    path('clients/<int:pk>/service-contract/', views.service_contract, name='service_contract'),
    path('clients/<int:pk>/service-contract/create/', views.create_contract, name='create_contract'),
    path('clients/<int:pk>/service-contract/preview/', views.preview_contract_pdf, name='preview_contract_pdf'),
    path('clients/<int:pk>/contracts/<int:token_id>/download/', views.download_contract_pdf, name='download_contract_pdf'),
    path('clients/<int:pk>/send-service-contract/', views.send_service_contract, name='send_service_contract'),

    # Service Contract URLs (públicas)
    path('contracts/<str:token>/', views.view_service_contract, name='view_service_contract'),
    path('contracts/<str:token>/accept/', views.accept_service_contract, name='accept_service_contract'),
    path('contract/<str:token>/', views.public_contract, name='public_contract'),
    path('contract/<str:token>/sign/', views.sign_contract, name='sign_contract'),
    
    # Subscriptions URLs
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/create/', views.subscription_create, name='subscription_create'),
    path('subscriptions/<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('subscriptions/<int:pk>/update/', views.subscription_update, name='subscription_update'),
    path('subscriptions/<int:pk>/delete/', views.subscription_delete, name='subscription_delete'),
    path('subscriptions/<int:pk>/activate/', views.subscription_activate, name='subscription_activate'),
    path('subscriptions/<int:pk>/suspend/', views.subscription_suspend, name='subscription_suspend'),
    path('subscriptions/<int:pk>/cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('subscriptions/<int:pk>/deactivate/', views.subscription_deactivate, name='subscription_deactivate'),
    path('subscriptions/<int:pk>/renew/', views.subscription_renew, name='subscription_renew'),
    path('subscriptions/<int:subscription_pk>/events/<int:event_pk>/pay/', views.mark_payment_event_paid, name='mark_payment_event_paid'),

    # Calculadora URLs
    path('calculadoras/', views.calculadora_list, name='calculadora_list'),
    path('calculadoras/create/', views.calculadora_create, name='calculadora_create'),
    path('calculadoras/<int:pk>/', views.calculadora_detail, name='calculadora_detail'),
    path('calculadoras/<int:pk>/update/', views.calculadora_update, name='calculadora_update'),
    path('calculadoras/<int:pk>/delete/', views.calculadora_delete, name='calculadora_delete'),
    path('calculadoras/<int:pk>/pdf/', views.calculadora_pdf, name='calculadora_pdf'),
    path('calculadoras/<int:pk>/enviar-cotizacion/', views.enviar_cotizacion_email, name='enviar_cotizacion_email'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('calculadora/<int:pk>/generar-suscripciones/', views.generar_suscripciones, name='generar_suscripciones'),

    # Contact Messages URLs
    path('messages/', views.message_list, name='message_list'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/<int:pk>/archive/', views.message_archive, name='message_archive'),
    path('messages/<int:pk>/unarchive/', views.message_unarchive, name='message_unarchive'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),
    path('messages/<int:pk>/notes/', views.message_update_notes, name='message_update_notes'),
    path('messages/<int:pk>/meeting-link/', views.message_update_meeting_link, name='message_update_meeting_link'),

    # Agenda URLs
    path('agenda/', views.agenda_view, name='agenda_view'),
    path('agenda/appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('agenda/appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    path('agenda/appointments/<int:pk>/complete/', views.appointment_complete, name='appointment_complete'),
    path('agenda/toggle-block/', views.toggle_slot_block, name='toggle_slot_block'),
    path('agenda/block-full-day/', views.block_full_day, name='block_full_day'),
    path('agenda/unblock-full-day/', views.unblock_full_day, name='unblock_full_day'),
    path('agenda/available-slots/', views.get_available_slots, name='get_available_slots'),
]
