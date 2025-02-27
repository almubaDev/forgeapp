# forgeapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Count, Sum, Q
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import os
import re
import base64
import uuid
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import Application, Client, Subscription, Calculadora, ItemCalculo, ApplicationConfig, ServiceContractToken
from .forms import (
    ApplicationForm, ClientForm, SubscriptionForm, 
    CalculadoraForm, ItemCalculoForm, ApplicationConfigForm
)
from .markdown_processor import process_markdown_section
from checkout_counters.models import PaymentLink, Receipt

logger = logging.getLogger('forgeapp')

# Landing page
def landing(request):
    return render(request, 'forgeapp/landing.html')

# Contact form
def contact_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        # Enviar correo electrónico
        subject = f'Nuevo contacto desde ForgeApp: {name}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = settings.CONTACT_EMAIL
        
        # Crear contenido HTML
        html_content = render_to_string('forgeapp/email/contact_email.html', {
            'name': name,
            'email': email,
            'phone': phone,
            'message': message
        })
        
        # Enviar correo
        msg = EmailMultiAlternatives(subject, message, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        messages.success(request, 'Tu mensaje ha sido enviado. Te contactaremos pronto.')
        return redirect('forgeapp:landing')
    
    return redirect('forgeapp:landing')

# Dashboard
@login_required
def dashboard(request):
    # Obtener estadísticas
    total_clients = Client.objects.count()
    total_applications = Application.objects.count()
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(status='active').count()
    
    # Obtener clientes recientes
    recent_clients = Client.objects.all().order_by('-created_at')[:5]
    
    # Obtener aplicaciones recientes
    recent_applications = Application.objects.all().order_by('-created_at')[:5]
    
    # Obtener suscripciones recientes
    recent_subscriptions = Subscription.objects.all().order_by('-created_at')[:5]
    
    context = {
        'total_clients': total_clients,
        'total_applications': total_applications,
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'recent_clients': recent_clients,
        'recent_applications': recent_applications,
        'recent_subscriptions': recent_subscriptions
    }
    
    return render(request, 'forgeapp/dashboard.html', context)

# Application views
@login_required
def application_list(request):
    applications = Application.objects.all()
    return render(request, 'forgeapp/application_list.html', {'applications': applications})

@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)
    return render(request, 'forgeapp/application_detail.html', {'application': application})

@login_required
def application_create(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(request, 'Aplicación creada exitosamente.')
            return redirect('forgeapp:application_detail', pk=application.pk)
    else:
        form = ApplicationForm()
    return render(request, 'forgeapp/application_form.html', {'form': form, 'is_create': True})

@login_required
def application_update(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aplicación actualizada exitosamente.')
            return redirect('forgeapp:application_detail', pk=pk)
    else:
        form = ApplicationForm(instance=application)
    return render(request, 'forgeapp/application_form.html', {'form': form, 'application': application, 'is_create': False})

@login_required
def application_delete(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Aplicación eliminada exitosamente.')
        return redirect('forgeapp:application_list')
    return render(request, 'forgeapp/application_confirm_delete.html', {'application': application})

@login_required
def application_configs(request, pk):
    application = get_object_or_404(Application, pk=pk)
    configs = application.configs.all()
    return render(request, 'forgeapp/application_configs.html', {'application': application, 'configs': configs})

@login_required
def application_config_add(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.application = application
            config.save()
            messages.success(request, 'Configuración agregada exitosamente.')
            return redirect('forgeapp:application_configs', pk=pk)
    else:
        form = ApplicationConfigForm()
    return render(request, 'forgeapp/application_config_form.html', {'form': form, 'application': application})

@login_required
def application_config_edit(request, config_pk):
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    application = config.application
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada exitosamente.')
            return redirect('forgeapp:application_configs', pk=application.pk)
    else:
        form = ApplicationConfigForm(instance=config)
    return render(request, 'forgeapp/application_config_form.html', {'form': form, 'application': application, 'config': config})

@login_required
def application_config_delete(request, config_pk):
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    application = config.application
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Configuración eliminada exitosamente.')
        return redirect('forgeapp:application_configs', pk=application.pk)
    return render(request, 'forgeapp/application_config_confirm_delete.html', {'config': config, 'application': application})

# Client views
@login_required
def client_list(request):
    # Obtener todos los clientes con anotaciones para el número de suscripciones
    clients = Client.objects.all().annotate(
        total_subscriptions=Count('subscriptions'),
        active_subscriptions=Count('subscriptions', filter=Q(subscriptions__status='active'))
    )
    return render(request, 'forgeapp/client_list.html', {'clients': clients})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    # Obtener las suscripciones del cliente
    subscriptions = client.subscriptions.all()
    
    # Calcular valores para el resumen
    client.active_subscriptions = subscriptions.filter(status='active').count()
    client.total_subscriptions = subscriptions.count()
    client.total_value = subscriptions.filter(status='active').aggregate(Sum('price'))['price__sum'] or 0
    
    return render(request, 'forgeapp/client_detail.html', {
        'client': client,
        'subscriptions': subscriptions
    })

@login_required
def client_payment_history(request, pk):
    """
    Muestra el historial de pagos de un cliente.
    """
    client = get_object_or_404(Client, pk=pk)
    
    # Obtener todas las suscripciones del cliente
    subscriptions = client.subscriptions.all()
    
    # Obtener todos los enlaces de pago asociados a las suscripciones del cliente
    payment_links = PaymentLink.objects.filter(subscription__in=subscriptions).order_by('-created_at')
    
    # Obtener los recibos asociados a los enlaces de pago
    receipts = Receipt.objects.filter(payment_link__in=payment_links).select_related('payment_link')
    
    return render(request, 'forgeapp/client_payment_history.html', {
        'client': client,
        'payment_links': payment_links,
        'receipts': receipts
    })

@login_required
def client_contracts(request, pk):
    """
    Muestra la lista de contratos firmados de un cliente.
    """
    client = get_object_or_404(Client, pk=pk)
    
    # Buscar todos los tokens de contrato que hayan sido usados (firmados)
    tokens = ServiceContractToken.objects.filter(
        client=client,
        used=True
    ).order_by('-used_at')
    
    if not tokens.exists():
        messages.warning(request, 'Este cliente no tiene contratos firmados.')
        return redirect('forgeapp:client_detail', pk=pk)
    
    # Obtener las aplicaciones asociadas a los contratos
    contracts = []
    for token in tokens:
        try:
            application = Application.objects.get(pk=token.application_id)
            contracts.append({
                'token': token,
                'application': application,
                'subscription_type': 'Mensual' if token.subscription_type == 'monthly' else 'Anual',
                'used_at': token.used_at,
                'price': token.price
            })
        except Application.DoesNotExist:
            # Si la aplicación no existe, omitir este contrato
            continue
    
    # Renderizar la vista de la lista de contratos
    return render(request, 'forgeapp/client_contracts.html', {
        'client': client,
        'contracts': contracts
    })

@login_required
def view_client_contract(request, pk, token_id):
    """
    Muestra un contrato específico firmado por un cliente.
    """
    client = get_object_or_404(Client, pk=pk)
    token_obj = get_object_or_404(ServiceContractToken, id=token_id, client=client, used=True)
    
    # Obtener la aplicación asociada al contrato
    application = get_object_or_404(Application, pk=token_obj.application_id)
    
    # Renderizar la vista del contrato firmado
    return render(request, 'forgeapp/public_service_contract.html', {
        'client': client,
        'application': application,
        'subscription_type': token_obj.subscription_type,
        'token': token_obj.token,
        'token_obj': token_obj,
        'is_preview': False,
        'is_accepted': True,
        'is_admin_view': True  # Indicar que es una vista de administrador
    })

@login_required
def service_contract(request, pk):
    """
    Muestra el formulario de contrato de servicio para un cliente.
    """
    client = get_object_or_404(Client, pk=pk)
    
    # Obtener todas las aplicaciones disponibles
    applications = Application.objects.all()
    
    return render(request, 'forgeapp/service_contract.html', {
        'client': client,
        'applications': applications,
        'is_preview': True
    })

@login_required
def send_service_contract(request, pk):
    """
    Envía el contrato de servicio al cliente por email.
    """
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        application_id = request.POST.get('application')
        subscription_type = request.POST.get('subscription_type')
        price_str = request.POST.get('price', '0')
        
        # Validar datos
        if not application_id or not subscription_type or not price_str:
            messages.error(request, 'Por favor complete todos los campos requeridos.')
            return redirect('forgeapp:service_contract', pk=pk)
        
        try:
            # Obtener la aplicación seleccionada
            application = Application.objects.get(pk=application_id)
            
            # Procesar el precio
            price_str = ''.join(c for c in price_str if c.isdigit())
            price = int(price_str) if price_str else 0
            
            if price <= 0:
                messages.error(request, 'Por favor ingrese un valor válido para la suscripción.')
                return redirect('forgeapp:service_contract', pk=pk)
            
            # Crear un token para el contrato
            token = ServiceContractToken.objects.create(
                client=client,
                application_id=application_id,
                subscription_type=subscription_type,
                token=str(uuid.uuid4()),
                expires_at=timezone.now() + timedelta(days=7),
                price=price  # Guardar el precio en el token
            )
            
            # Actualizar el estado del contrato del cliente
            client.contract_status = 'pending'
            client.save()
            
            # Generar URL para el contrato
            contract_url = request.build_absolute_uri(
                reverse('forgeapp:view_service_contract', kwargs={'token': token.token})
            )
            
            # Enviar email al cliente
            subject = f'Contrato de Servicio ForgeApp - {application.name}'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = client.email
            
            # Crear contenido HTML
            html_content = render_to_string('forgeapp/email/service_contract_email.html', {
                'client': client,
                'application': application,
                'subscription_type': 'Mensual' if subscription_type == 'monthly' else 'Anual',
                'contract_url': contract_url,
                'expires_at': token.expires_at.strftime('%d/%m/%Y %H:%M')
            })
            
            # Crear contenido de texto plano
            text_content = f"""
            Estimado/a {client.name},
            
            Le enviamos el contrato de servicio para la aplicación {application.name}.
            
            Para revisar y aceptar el contrato, por favor visite el siguiente enlace:
            {contract_url}
            
            Este enlace expirará el {token.expires_at.strftime('%d/%m/%Y %H:%M')}.
            
            Saludos cordiales,
            Equipo ForgeApp
            """
            
            # Enviar correo
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            messages.success(request, f'Contrato enviado exitosamente a {client.email}.')
            return redirect('forgeapp:client_detail', pk=pk)
            
        except Application.DoesNotExist:
            messages.error(request, 'La aplicación seleccionada no existe.')
            return redirect('forgeapp:service_contract', pk=pk)
        except Exception as e:
            messages.error(request, f'Error al enviar el contrato: {str(e)}')
            return redirect('forgeapp:service_contract', pk=pk)
    
    # Si no es POST, redirigir al formulario
    return redirect('forgeapp:service_contract', pk=pk)

def view_service_contract(request, token):
    """
    Permite al cliente ver el contrato de servicio.
    """
    try:
        # Obtener el token
        token_obj = get_object_or_404(ServiceContractToken, token=token)
        
        # Obtener el cliente y la aplicación
        client = token_obj.client
        application = get_object_or_404(Application, pk=token_obj.application_id)
        
        # Verificar si el token ha expirado
        if token_obj.expires_at < timezone.now():
            messages.error(request, 'El enlace ha expirado. Por favor solicite un nuevo contrato.')
            # Usar la plantilla pública para el contrato
            return render(request, 'forgeapp/public_service_contract.html', {
                'client': client,
                'application': application,
                'subscription_type': token_obj.subscription_type,
                'token': token,
                'is_preview': False,
                'is_expired': True
            })
        
        # Verificar si el token ya fue usado
        if token_obj.used:
            # En lugar de redirigir, mostrar la página con un mensaje
            messages.info(request, 'Este contrato ya ha sido aceptado. No es necesario volver a aceptarlo.')
            
            # Buscar la suscripción asociada a este contrato
            try:
                subscription = Subscription.objects.filter(
                    client=client,
                    application=application,
                    payment_type=token_obj.subscription_type
                ).latest('created_at')
                
                return render(request, 'forgeapp/public_service_contract.html', {
                    'client': client,
                    'application': application,
                    'subscription_type': token_obj.subscription_type,
                    'token': token,
                    'is_preview': False,
                    'is_accepted': True,
                    'subscription': subscription
                })
            except Subscription.DoesNotExist:
                # Si no se encuentra la suscripción, mostrar la página sin ella
                return render(request, 'forgeapp/public_service_contract.html', {
                    'client': client,
                    'application': application,
                    'subscription_type': token_obj.subscription_type,
                    'token': token,
                    'token_obj': token_obj,  # Pasar el objeto token completo
                    'is_preview': False,
                    'is_accepted': True
                })
        
        # Si el token es válido y no ha sido usado, mostrar el contrato
        return render(request, 'forgeapp/public_service_contract.html', {
            'client': client,
            'application': application,
            'subscription_type': token_obj.subscription_type,
            'token': token,
            'token_obj': token_obj,  # Pasar el objeto token completo
            'is_preview': False
        })
    except ServiceContractToken.DoesNotExist:
        # Si el token no existe, mostrar un mensaje de error
        logger.error(f"Token no encontrado: {token}")
        messages.error(request, 'El enlace no es válido. Por favor solicite un nuevo contrato.')
        return render(request, 'forgeapp/public_service_contract.html', {
            'is_preview': False,
            'is_error': True,
            'error_message': 'Token no encontrado'
        })
    except Exception as e:
        # Registrar el error
        logger.error(f"Error al ver el contrato: {str(e)}")
        messages.error(request, 'Ha ocurrido un error al cargar el contrato. Por favor contacte a soporte.')
        # En lugar de redirigir a la landing page, mostrar una página de error
        return render(request, 'forgeapp/public_service_contract.html', {
            'is_preview': False,
            'is_error': True,
            'error_message': str(e)
        })

def accept_service_contract(request, token):
    """
    Permite al cliente aceptar el contrato de servicio.
    """
    try:
        # Obtener el token
        token_obj = get_object_or_404(ServiceContractToken, token=token)
        
        # Obtener el cliente y la aplicación
        client = token_obj.client
        application = get_object_or_404(Application, pk=token_obj.application_id)
        
        # Verificar si el token ha expirado
        if token_obj.expires_at < timezone.now():
            messages.error(request, 'El enlace ha expirado. Por favor solicite un nuevo contrato.')
            return render(request, 'forgeapp/public_service_contract.html', {
                'client': client,
                'application': application,
                'subscription_type': token_obj.subscription_type,
                'token': token,
                'is_preview': False,
                'is_expired': True
            })
        
        # Verificar si el token ya fue usado
        if token_obj.used:
            messages.info(request, 'Este contrato ya ha sido aceptado. No es necesario volver a aceptarlo.')
            
            # Buscar la suscripción asociada a este contrato
            try:
                subscription = Subscription.objects.filter(
                    client=client,
                    application=application,
                    payment_type=token_obj.subscription_type
                ).latest('created_at')
                
                return render(request, 'forgeapp/public_service_contract.html', {
                    'client': client,
                    'application': application,
                    'subscription_type': token_obj.subscription_type,
                    'token': token,
                    'is_preview': False,
                    'is_accepted': True,
                    'subscription': subscription
                })
            except Subscription.DoesNotExist:
                # Si no se encuentra la suscripción, mostrar la página sin ella
                return render(request, 'forgeapp/public_service_contract.html', {
                    'client': client,
                    'application': application,
                    'subscription_type': token_obj.subscription_type,
                    'token': token,
                    'is_preview': False,
                    'is_accepted': True
                })
        
        if request.method == 'POST':
            # Verificar si el cliente aceptó los términos
            accept_terms = request.POST.get('accept_terms') == 'on'
            accept_marketing = request.POST.get('accept_marketing') == 'on'
            
            if not accept_terms:
                messages.error(request, 'Debe aceptar los términos y condiciones para continuar.')
                return redirect('forgeapp:view_service_contract', token=token)
            
            try:
                # Actualizar el cliente si aceptó recibir marketing
                if accept_marketing and not client.accept_marketing:
                    client.accept_marketing = True
                    client.save()
                
                # Guardar el precio en el token para referencia futura
                try:
                    price_str = request.POST.get('price', '0')
                    # Eliminar cualquier carácter no numérico (como $, ., etc.)
                    price_str = ''.join(c for c in price_str if c.isdigit())
                    price = int(price_str) if price_str else 0
                    
                    if price > 0:
                        token_obj.price = price
                except (ValueError, TypeError):
                    # Si hay un error al convertir el precio, no hacer nada
                    pass
                
                # Marcar el token como usado
                token_obj.used = True
                token_obj.used_at = timezone.now()
                token_obj.save()
                
                # Actualizar el estado del contrato del cliente
                client.contract_status = 'accepted'
                client.save()
                
                # Generar PDF del contrato
                from pdf_generator.views import generar_pdf_contrato_buffer
                from io import BytesIO
                import tempfile
                
                # Generar el PDF en un buffer
                pdf_buffer = BytesIO()
                generar_pdf_contrato_buffer(token_obj, pdf_buffer)
                pdf_buffer.seek(0)
                
                # Crear un archivo temporal para el PDF
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(pdf_buffer.getvalue())
                temp_file.close()
                
                # Enviar email de confirmación con el PDF adjunto
                subject = f'Confirmación de Contrato - {application.name}'
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = client.email
                
                # Crear contenido HTML
                html_content = render_to_string('forgeapp/email/contract_confirmation_email.html', {
                    'client': client,
                    'application': application,
                    'subscription_type': 'Mensual' if token_obj.subscription_type == 'monthly' else 'Anual'
                })
                
                # Crear contenido de texto plano
                text_content = f"""
                Estimado/a {client.name},
                
                Gracias por aceptar el contrato de servicio para la aplicación {application.name}.
                
                Adjunto encontrará una copia del contrato firmado en formato PDF.
                
                Nuestro equipo se pondrá en contacto con usted para activar su suscripción y proporcionarle instrucciones para realizar el primer pago.
                
                Saludos cordiales,
                Equipo ForgeApp
                """
                
                # Enviar correo con el PDF adjunto
                try:
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
                    msg.attach_alternative(html_content, "text/html")
                    
                    # Leer el archivo PDF y adjuntarlo con un nombre personalizado
                    with open(temp_file.name, 'rb') as f:
                        pdf_content = f.read()
                        msg.attach(f'contrato_{client.name}_{token_obj.token[:8]}.pdf', pdf_content, 'application/pdf')
                    
                    msg.send()
                    logger.info(f"Correo enviado exitosamente a {to_email} con el contrato adjunto")
                except Exception as mail_error:
                    # Registrar el error pero continuar con el proceso
                    logger.error(f"Error al enviar el correo: {str(mail_error)}")
                    # No mostrar este error al usuario para no interrumpir el flujo
                
                # Eliminar el archivo temporal
                import os
                os.unlink(temp_file.name)
                
                # Mostrar mensaje de éxito y redirigir a la página de contrato aceptado
                messages.success(request, 'Contrato aceptado exitosamente. Nuestro equipo se pondrá en contacto con usted para activar su suscripción.')
                
                # En lugar de redirigir a la landing page, mostrar la página de contrato aceptado
                return render(request, 'forgeapp/public_service_contract.html', {
                    'client': client,
                    'application': application,
                    'subscription_type': token_obj.subscription_type,
                    'token': token,
                    'token_obj': token_obj,  # Pasar el objeto token completo
                    'is_preview': False,
                    'is_accepted': True,
                    'just_accepted': True
                })
                
            except Exception as e:
                # Registrar el error
                logger.error(f"Error al procesar el contrato: {str(e)}")
                messages.error(request, 'Ha ocurrido un error al procesar el contrato. Por favor contacte a soporte.')
                return redirect('forgeapp:view_service_contract', token=token)
        
        # Si no es POST, redirigir a la vista del contrato
        return redirect('forgeapp:view_service_contract', token=token)
    
    except Exception as e:
        # Registrar el error
        logger.error(f"Error al acceder al contrato: {str(e)}")
        messages.error(request, 'Ha ocurrido un error al acceder al contrato. Por favor contacte a soporte.')
        # En lugar de redirigir a la landing page, mostrar una página de error
        return render(request, 'forgeapp/public_service_contract.html', {
            'is_preview': False,
            'is_error': True,
            'error_message': str(e)
        })

@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('forgeapp:client_detail', pk=client.pk)
    else:
        form = ClientForm()
    return render(request, 'forgeapp/client_form.html', {'form': form, 'is_create': True})

@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('forgeapp:client_detail', pk=pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'forgeapp/client_form.html', {'form': form, 'client': client, 'is_create': False})

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('forgeapp:client_list')
    return render(request, 'forgeapp/client_confirm_delete.html', {'client': client})

# Subscription views
@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.all()
    return render(request, 'forgeapp/subscription_list.html', {'subscriptions': subscriptions})

@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    return render(request, 'forgeapp/subscription_detail.html', {'subscription': subscription})

@login_required
def subscription_create(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, 'Suscripción creada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=subscription.pk)
    else:
        form = SubscriptionForm()
    return render(request, 'forgeapp/subscription_form.html', {'form': form, 'is_create': True})

@login_required
def subscription_update(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Suscripción actualizada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=pk)
    else:
        form = SubscriptionForm(instance=subscription)
    return render(request, 'forgeapp/subscription_form.html', {'form': form, 'subscription': subscription, 'is_create': False})

@login_required
def subscription_delete(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'Suscripción eliminada exitosamente.')
        return redirect('forgeapp:subscription_list')
    return render(request, 'forgeapp/subscription_confirm_delete.html', {'subscription': subscription})

@login_required
def subscription_activate(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    
    logger.info(f"INICIO: Activando suscripción {subscription.reference_id} (ID: {subscription.id})")
    logger.info(f"Estado actual: {subscription.status}")
    logger.info(f"Cliente: {subscription.client.name} (ID: {subscription.client.id})")
    logger.info(f"Aplicación: {subscription.application.name} (ID: {subscription.application.id})")
    
    try:
        # Cambiar estado a activo
        subscription.status = 'active'
        subscription.save()
        logger.info(f"Estado cambiado a 'active' y guardado")
        
        # Generar enlace de pago
        try:
            logger.info(f"Intentando generar enlace de pago con request...")
            payment_link = subscription.generate_payment_link(request=request)
            
            if payment_link:
                # Actualizar fechas de pago
                subscription.update_payment_dates()
                
                # Enviar email con enlace de pago
                try:
                    subscription.send_payment_email(payment_link)
                    messages.success(request, 'Suscripción activada y enlace de pago enviado exitosamente.')
                except Exception as email_error:
                    logger.error(f"Error al enviar email de pago: {str(email_error)}")
                    messages.warning(request, 'Suscripción activada, pero hubo un error al enviar el email con el enlace de pago.')
            else:
                messages.warning(request, 'Suscripción activada, pero no se pudo generar el enlace de pago.')
        except Exception as payment_error:
            logger.error(f"Error al generar enlace de pago: {str(payment_error)}")
            messages.warning(request, f'Suscripción activada, pero hubo un error al generar el enlace de pago: {str(payment_error)}')
    except Exception as e:
        logger.error(f"Error al activar suscripción: {str(e)}")
        messages.error(request, f'Error al activar la suscripción: {str(e)}')
    
    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def subscription_suspend(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    subscription.status = 'suspended'
    subscription.save()
    messages.success(request, 'Suscripción suspendida exitosamente.')
    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def subscription_cancel(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    subscription.status = 'cancelled'
    subscription.save()
    messages.success(request, 'Suscripción cancelada exitosamente.')
    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def subscription_deactivate(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    subscription.status = 'inactive'
    subscription.save()
    messages.success(request, 'Suscripción desactivada exitosamente.')
    return redirect('forgeapp:subscription_detail', pk=pk)

# Calculadora views
@login_required
def calculadora_list(request):
    calculadoras = Calculadora.objects.all()
    return render(request, 'forgeapp/calculadora_list.html', {'calculadoras': calculadoras})

@login_required
def calculadora_detail(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    items = calculadora.items.all()
    
    if request.method == 'POST':
        item_form = ItemCalculoForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.calculadora = calculadora
            item.save()
            messages.success(request, 'Item agregado exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    else:
        item_form = ItemCalculoForm()
    
    return render(request, 'forgeapp/calculadora_detail.html', {
        'calculadora': calculadora,
        'items': items,
        'item_form': item_form
    })

@login_required
def calculadora_create(request):
    if request.method == 'POST':
        form = CalculadoraForm(request.POST)
        if form.is_valid():
            calculadora = form.save()
            messages.success(request, 'Calculadora creada exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=calculadora.pk)
    else:
        form = CalculadoraForm()
    return render(request, 'forgeapp/calculadora_form.html', {'form': form, 'is_create': True})

@login_required
def calculadora_update(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    if request.method == 'POST':
        form = CalculadoraForm(request.POST, instance=calculadora)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calculadora actualizada exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    else:
        form = CalculadoraForm(instance=calculadora)
    return render(request, 'forgeapp/calculadora_form.html', {'form': form, 'calculadora': calculadora, 'is_create': False})

@login_required
def calculadora_delete(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    if request.method == 'POST':
        calculadora.delete()
        messages.success(request, 'Calculadora eliminada exitosamente.')
        return redirect('forgeapp:calculadora_list')
    return render(request, 'forgeapp/calculadora_confirm_delete.html', {'calculadora': calculadora})

@login_required
def item_delete(request, pk):
    item = get_object_or_404(ItemCalculo, pk=pk)
    calculadora_pk = item.calculadora.pk
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item eliminado exitosamente.')
        return redirect('forgeapp:calculadora_detail', pk=calculadora_pk)
    return render(request, 'forgeapp/item_confirm_delete.html', {'item': item})

@login_required
def calculadora_pdf(request, pk):
    """
    Redirige a la vista de generación de PDF en la aplicación pdf_generator.
    """
    return redirect('pdf_generator:generar_pdf_propuesta', pk=pk)

@login_required
def enviar_cotizacion_email(request, pk):
    """
    Genera el PDF de la calculadora y lo envía por correo al cliente.
    """
    try:
        # Obtener la calculadora
        calculadora = get_object_or_404(Calculadora, pk=pk)
        
        # Verificar que la calculadora tenga un cliente con email
        if not calculadora.client or not calculadora.client.email:
            messages.error(request, 'El cliente no tiene un correo electrónico configurado.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
        
        # Generar el PDF temporalmente
        from io import BytesIO
        from django.core.files.base import ContentFile
        import tempfile
        import os
        from django.core.mail import EmailMessage
        from pdf_generator.views import generar_pdf_propuesta_buffer
        
        # Generar el PDF en un buffer
        pdf_buffer = BytesIO()
        generar_pdf_propuesta_buffer(calculadora, pdf_buffer)
        pdf_buffer.seek(0)
        
        # Crear un archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_buffer.getvalue())
        temp_file.close()
        
        # Preparar el correo
        subject = f'Cotización: {calculadora.nombre}'
        
        # Ruta al logo
        logo_path = os.path.join('static', 'img', 'logo.png')
        
        # Crear el email con HTML
        from django.core.mail import EmailMultiAlternatives
        
        # Texto plano como fallback
        text_content = f"""
        Estimado/a {calculadora.client.name},
        
        Adjunto encontrará la cotización solicitada para {calculadora.nombre} y la descripción de la aplicación a desarrollar.
        
        Si tiene alguna pregunta o necesita más información, no dude en contactarnos.
        
        Saludos cordiales,
        Equipo ForgeApp
        """
        
        # Renderizar la plantilla HTML
        html_content = render_to_string('forgeapp/email/cotizacion_email.html', {
            'calculadora': calculadora,
            'client': calculadora.client
        })
        
        # Crear el email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[calculadora.client.email],
        )
        
        # Simplificar el enfoque para el correo HTML
        email.content_subtype = 'html'  # Establecer el tipo de contenido principal como HTML
        
        # Agregar contenido HTML
        email.attach_alternative(html_content, "text/html")
        
        # Adjuntar el PDF (solo una vez)
        email.attach_file(temp_file.name)
        
        # Enviar el correo
        email.send()
        
        # Eliminar el archivo temporal
        os.unlink(temp_file.name)
        
        messages.success(request, f'Cotización enviada exitosamente a {calculadora.client.email}')
        return redirect('forgeapp:calculadora_detail', pk=pk)
        
    except Exception as e:
        logger.error(f"Error al enviar cotización por email: {str(e)}")
        messages.error(request, f'Error al enviar la cotización: {str(e)}')
        return redirect('forgeapp:calculadora_detail', pk=pk)

@login_required
def generar_suscripciones(request, pk):
    """
    Genera o actualiza suscripciones a partir de una calculadora.
    """
    calculadora = get_object_or_404(Calculadora, pk=pk)
    
    if request.method == 'POST':
        try:
            # Verificar que la calculadora tenga un cliente y una aplicación
            if not calculadora.client:
                messages.error(request, 'La calculadora debe tener un cliente asignado.')
                return redirect('forgeapp:calculadora_detail', pk=pk)
            
            if not hasattr(calculadora, 'application') or not calculadora.application:
                messages.error(request, 'La calculadora debe tener una aplicación asignada.')
                return redirect('forgeapp:calculadora_detail', pk=pk)
            
            # Obtener datos del formulario
            start_date_str = request.POST.get('start_date')
            auto_renewal = request.POST.get('auto_renewal') == 'on'
            
            # Validar fecha de inicio
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                start_date = timezone.now().date()
            
            # Usar el método del modelo para generar o actualizar suscripciones
            sub_mensual, sub_anual = calculadora.generar_suscripciones(start_date, auto_renewal)
            
            # Verificar si ya existían suscripciones
            existing_subscriptions = Subscription.objects.filter(calculadora=calculadora)
            
            if existing_subscriptions.count() > 0:
                messages.success(request, 'Suscripciones actualizadas exitosamente.')
            else:
                messages.success(request, 'Suscripciones generadas exitosamente.')
            
            # Redirigir a la suscripción mensual
            if sub_mensual:
                return redirect('forgeapp:subscription_detail', pk=sub_mensual.pk)
            elif sub_anual:
                return redirect('forgeapp:subscription_detail', pk=sub_anual.pk)
            else:
                return redirect('forgeapp:calculadora_detail', pk=pk)
            
        except Exception as e:
            logger.error(f"Error al generar suscripciones: {str(e)}")
            messages.error(request, f'Error al generar las suscripciones: {str(e)}')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    
    # Si no es POST, redirigir a la vista de detalle
    return redirect('forgeapp:calculadora_detail', pk=pk)
