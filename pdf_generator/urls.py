from django.urls import path
from . import views

app_name = 'pdf_generator'

urlpatterns = [
    path('propuesta/<int:pk>/', views.generar_pdf_propuesta, name='generar_pdf_propuesta'),
    path('recibo/<int:pk>/', views.generar_pdf_recibo, name='generar_recibo'),
    path('comprobante/verificar/<str:receipt_number>/<str:verification_code>/', views.verificar_comprobante, name='verificar_comprobante'),
    path('comprobante/verificar/', views.verificar_comprobante_form, name='verificar_comprobante_form'),
]
