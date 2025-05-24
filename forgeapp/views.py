from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
from django.db import models
import logging
import os
from .models import (
    Subscription, Calculadora, ItemCalculo, Payment,
    Application, ApplicationConfig, Client, ServiceContractToken
)
from .forms import (
    SubscriptionForm, CalculadoraForm, ItemCalculoForm,
    ApplicationForm, ApplicationConfigForm, ClientForm
)

logger = logging.getLogger('forgeapp')

def landing(request):
    """Vista de la página de inicio"""
    return render(request, 'forgeapp/landing.html')

def contact_form(request):
    """Vista del formulario de contacto"""
    return render(request, 'forgeapp/contact_form.html')

@login_required
def dashboard(request):
    """Vista del panel de control"""
    # Obtener estadísticas
    total_clients = Client.objects.count()
    active_subscriptions = Subscription.objects.filter(status='active').count()
    total_applications = Application.objects.count()
    
    # Obtener datos recientes
    recent_clients = Client.objects.order_by('-created_at')[:5]
    recent_subscriptions = Subscription.objects.order_by('-created_at')[:5]
    
    return render(request, 'forgeapp/dashboard.html', {
        'total_clients': total_clients,
        'active_subscriptions': active_subscriptions,
        'total_applications': total_applications,
        'recent_clients': recent_clients,
        'recent_subscriptions': recent_subscriptions
    })

# Application views
@login_required
def application_list(request):
    """Lista de aplicaciones"""
    applications = Application.objects.all()
    
    # Añadir estadísticas a cada aplicación
    for app in applications:
        app.total_subscriptions = Subscription.objects.filter(application=app).count()
        app.active_subscriptions = Subscription.objects.filter(application=app, status='active').count()
        app.total_revenue = Subscription.objects.filter(application=app, status='active', payment_type='monthly').aggregate(models.Sum('price'))['price__sum'] or 0
    
    return render(request, 'forgeapp/application_list.html', {'applications': applications})

@login_required
def application_detail(request, pk):
    """Detalle de una aplicación"""
    application = get_object_or_404(Application, pk=pk)
    
    # Obtener estadísticas
    application.total_subscriptions = Subscription.objects.filter(application=application).count()
    application.active_subscriptions = Subscription.objects.filter(application=application, status='active').count()
    application.total_revenue = Subscription.objects.filter(application=application, status='active', payment_type='monthly').aggregate(models.Sum('price'))['price__sum'] or 0
    
    # Obtener suscripciones
    subscriptions = Subscription.objects.filter(application=application).order_by('-created_at')
    
    return render(request, 'forgeapp/application_detail.html', {
        'application': application,
        'subscriptions': subscriptions
    })

@login_required
def application_create(request):
    """Crear una nueva aplicación"""
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(request, 'Aplicación creada exitosamente.')
            return redirect('forgeapp:application_detail', pk=application.pk)
    else:
        form = ApplicationForm()
    
    cancel_url = request.META.get('HTTP_REFERER', 'forgeapp:application_list')
    return render(request, 'forgeapp/application_form.html', {'form': form, 'cancel_url': cancel_url})

@login_required
def application_update(request, pk):
    """Actualizar una aplicación"""
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aplicación actualizada exitosamente.')
            return redirect('forgeapp:application_detail', pk=pk)
    else:
        form = ApplicationForm(instance=application)
    
    cancel_url = request.META.get('HTTP_REFERER', f'forgeapp:application_detail')
    return render(request, 'forgeapp/application_form.html', {'form': form, 'application': application, 'cancel_url': cancel_url})

@login_required
def application_delete(request, pk):
    """Eliminar una aplicación"""
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Aplicación eliminada exitosamente.')
        return redirect('forgeapp:application_list')
    return render(request, 'forgeapp/application_confirm_delete.html', {'application': application})

@login_required
def application_configs(request, pk):
    """Lista de configuraciones de una aplicación"""
    application = get_object_or_404(Application, pk=pk)
    configs = application.configs.all()
    return render(request, 'forgeapp/application_configs.html', {
        'application': application,
        'configs': configs
    })

@login_required
def application_config_add(request, pk):
    """Agregar una configuración a una aplicación"""
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
    return render(request, 'forgeapp/application_config_form.html', {
        'form': form,
        'application': application
    })

@login_required
def application_config_edit(request, config_pk):
    """Editar una configuración"""
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada exitosamente.')
            return redirect('forgeapp:application_configs', pk=config.application.pk)
    else:
        form = ApplicationConfigForm(instance=config)
    return render(request, 'forgeapp/application_config_form.html', {
        'form': form,
        'config': config,
        'application': config.application
    })

@login_required
def application_config_delete(request, config_pk):
    """Eliminar una configuración"""
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    application_pk = config.application.pk
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Configuración eliminada exitosamente.')
        return redirect('forgeapp:application_configs', pk=application_pk)
    return render(request, 'forgeapp/application_config_confirm_delete.html', {
        'config': config,
        'application': config.application
    })

# Client views
@login_required
def client_list(request):
    """Lista de clientes"""
    clients = Client.objects.all()
    
    # Añadir estadísticas a cada cliente
    for client in clients:
        client.total_subscriptions = Subscription.objects.filter(client=client).count()
        client.active_subscriptions = Subscription.objects.filter(client=client, status='active').count()
    
    return render(request, 'forgeapp/client_list.html', {'clients': clients})

@login_required
def client_detail(request, pk):
    """Detalle de un cliente"""
    client = get_object_or_404(Client, pk=pk)
    
    # Obtener suscripciones
    subscriptions = Subscription.objects.filter(client=client).order_by('-created_at')
    
    # Calcular estadísticas
    client.total_subscriptions = subscriptions.count()
    client.active_subscriptions = subscriptions.filter(status='active').count()
    
    # Calcular valor total mensual
    client.total_value = subscriptions.filter(status='active', payment_type='monthly').aggregate(models.Sum('price'))['price__sum'] or 0
    
    return render(request, 'forgeapp/client_detail.html', {
        'client': client,
        'subscriptions': subscriptions
    })

@login_required
def client_create(request):
    """Crear un nuevo cliente"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('forgeapp:client_detail', pk=client.pk)
    else:
        form = ClientForm()
    
    cancel_url = request.META.get('HTTP_REFERER', 'forgeapp:client_list')
    return render(request, 'forgeapp/client_form.html', {'form': form, 'cancel_url': cancel_url})

@login_required
def client_update(request, pk):
    """Actualizar un cliente"""
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('forgeapp:client_detail', pk=pk)
    else:
        form = ClientForm(instance=client)
    
    cancel_url = request.META.get('HTTP_REFERER', f'forgeapp:client_detail')
    return render(request, 'forgeapp/client_form.html', {'form': form, 'client': client, 'cancel_url': cancel_url})

@login_required
def client_delete(request, pk):
    """Eliminar un cliente"""
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('forgeapp:client_list')
    return render(request, 'forgeapp/client_confirm_delete.html', {'client': client})

@login_required
def client_payment_history(request, pk):
    """Historial de pagos de un cliente"""
    client = get_object_or_404(Client, pk=pk)
    
    # Ajustado para usar finance_payments en lugar de payments
    from finance.models import Payment as FinancePayment
    payments = FinancePayment.objects.filter(subscription__client=client).order_by('-payment_date')
    
    return render(request, 'forgeapp/client_payment_history.html', {
        'client': client,
        'payments': payments
    })

@login_required
def client_contracts(request, pk):
    """Contratos de un cliente"""
    client = get_object_or_404(Client, pk=pk)
    contracts = ServiceContractToken.objects.filter(client=client, used=True).order_by('-used_at')
    
    # Preparar datos para la plantilla
    contract_list = []
    for token in contracts:
        try:
            app = Application.objects.get(pk=token.application_id)
            contract_list.append({
                'application': app,
                'subscription_type': 'Mensual' if token.subscription_type == 'monthly' else 'Anual',
                'token': token,
                'price': token.price
            })
        except Application.DoesNotExist:
            # Si la aplicación no existe
            continue
    
    return render(request, 'forgeapp/client_contracts.html', {
        'client': client,
        'contracts': contract_list
    })

@login_required
def view_client_contract(request, pk, token_id):
    """Ver un contrato específico de un cliente"""
    client = get_object_or_404(Client, pk=pk)
    token = get_object_or_404(ServiceContractToken, pk=token_id, client=client)
    
    # Obtener la aplicación
    try:
        application = Application.objects.get(pk=token.application_id)
    except Application.DoesNotExist:
        application = None
    
    # Obtener la suscripción relacionada, si existe
    subscription = Subscription.objects.filter(
        client=client,
        application_id=token.application_id,
        payment_type=token.subscription_type
    ).first()
    
    return render(request, 'forgeapp/service_contract.html', {
        'client': client,
        'token_obj': token,
        'application': application,
        'subscription_type': token.subscription_type,
                'subscription': None,  # Ya no se crea suscripción al aceptar contrato
        'is_accepted': True,
        'just_accepted': False
    })

@login_required
def service_contract(request, pk):
    """Generar contrato de servicio (vista de administrador)"""
    client = get_object_or_404(Client, pk=pk)
    applications = Application.objects.all()
    
    return render(request, 'forgeapp/service_contract.html', {
        'client': client,
        'applications': applications,
        'is_preview': True
    })

@login_required
def send_service_contract(request, pk):
    """Enviar contrato de servicio por email"""
    import uuid
    from django.urls import reverse
    
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        application_id = request.POST.get('application')
        subscription_type = request.POST.get('subscription_type')
        price = request.POST.get('price')
        
        # Validar datos
        if not application_id or not subscription_type:
            messages.error(request, 'Por favor complete todos los campos.')
            return redirect('forgeapp:service_contract', pk=client.pk)
        
        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            messages.error(request, 'La aplicación seleccionada no existe.')
            return redirect('forgeapp:service_contract', pk=client.pk)
        
        # Crear token
        token = uuid.uuid4().hex
        expires_at = timezone.now() + timezone.timedelta(days=7)
        
        # Guardar token en la base de datos
        token_obj = ServiceContractToken.objects.create(
            client=client,
            application_id=application_id,
            subscription_type=subscription_type,
            token=token,
            expires_at=expires_at,
            price=price
        )
        
        # Generar URL del contrato
        contract_url = request.build_absolute_uri(
            reverse('forgeapp:view_service_contract', kwargs={'token': token})
        )
        
        # Enviar correo electrónico
        from django.core.mail import send_mail
        
        subject = f'ForgeApp: Contrato de Servicio - {application.name}'
        html_message = render_to_string('forgeapp/email/service_contract_email.html', {
            'client': client,
            'application': application,
            'subscription_type': 'Mensual' if subscription_type == 'monthly' else 'Anual',
            'contract_url': contract_url,
            'expires_at': expires_at.strftime('%d/%m/%Y %H:%M')
        })
        
        try:
            send_mail(
                subject=subject,
                message='',  # Mensaje en texto plano (vacío)
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                html_message=html_message,
                fail_silently=False
            )
            messages.success(request, f'Contrato enviado exitosamente a {client.email}')
        except Exception as e:
            logger.error(f"Error al enviar correo de contrato: {str(e)}")
            messages.error(request, f'Error al enviar el correo: {str(e)}')
        
        return redirect('forgeapp:client_detail', pk=client.pk)
    
    # Si no es POST, redirigir a la vista del contrato
    return redirect('forgeapp:service_contract', pk=client.pk)

def view_service_contract(request, token):
    """Ver contrato de servicio (vista pública)"""
    # Buscar token
    try:
        token_obj = ServiceContractToken.objects.get(token=token)
    except ServiceContractToken.DoesNotExist:
        return render(request, 'forgeapp/public_service_contract.html', {
            'is_error': True,
            'error_message': 'El token no existe o es inválido.'
        })
    
    # Verificar si ha expirado
    if token_obj.is_expired():
        return render(request, 'forgeapp/public_service_contract.html', {
            'is_expired': True,
            'token': token
        })
    
    # Verificar si ya ha sido usado
    if token_obj.used:
        try:
            # Obtener cliente y aplicación
            client = token_obj.client
            application = Application.objects.get(pk=token_obj.application_id)
            
            # Buscar suscripción relacionada
            subscription = Subscription.objects.filter(
                client=client,
                application=application,
                payment_type=token_obj.subscription_type
            ).first()
            
            return render(request, 'forgeapp/public_service_contract.html', {
                'is_accepted': True,
                'token_obj': token_obj,
                'client': client,
                'application': application,
                'subscription_type': token_obj.subscription_type,
                'subscription': None,  # Ya no se crea suscripción al aceptar contrato
                'token': token
            })
        except Application.DoesNotExist:
            return render(request, 'forgeapp/public_service_contract.html', {
                'is_error': True,
                'error_message': 'La aplicación asociada a este contrato no existe.'
            })
    
    # Si no ha expirado ni ha sido usado, mostrar contrato para aceptar
    try:
        client = token_obj.client
        application = Application.objects.get(pk=token_obj.application_id)
        
        return render(request, 'forgeapp/public_service_contract.html', {
            'client': client,
            'application': application,
            'subscription_type': token_obj.subscription_type,
            'token_obj': token_obj,
            'token': token
        })
    except Exception as e:
        logger.error(f"Error al mostrar contrato: {str(e)}")
        return render(request, 'forgeapp/public_service_contract.html', {
            'is_error': True,
            'error_message': str(e)
        })

def accept_service_contract(request, token):
    """Aceptar contrato de servicio"""
    # Buscar token
    try:
        token_obj = ServiceContractToken.objects.get(token=token)
    except ServiceContractToken.DoesNotExist:
        return render(request, 'forgeapp/public_service_contract.html', {
            'is_error': True,
            'error_message': 'El token no existe o es inválido.'
        })
    
    # Verificar si ha expirado
    if token_obj.is_expired():
        return render(request, 'forgeapp/public_service_contract.html', {
            'is_expired': True,
            'token': token
        })
    
    # Verificar si ya ha sido usado
    if token_obj.used:
        return redirect('forgeapp:view_service_contract', token=token)
    
    # Procesar la aceptación del contrato
    if request.method == 'POST':
        # Obtener datos del formulario
        accept_terms = request.POST.get('accept_terms') == 'on'
        accept_marketing = request.POST.get('accept_marketing') == 'on'
        
        if not accept_terms:
            messages.error(request, 'Debe aceptar los términos y condiciones.')
            return redirect('forgeapp:view_service_contract', token=token)
        
        try:
            # Actualizar token
            token_obj.used = True
            token_obj.used_at = timezone.now()
            token_obj.save()
            
            # Actualizar datos del cliente
            client = token_obj.client
            client.contract_status = 'accepted'
            client.accept_marketing = accept_marketing
            client.save()
            
            # Obtener la aplicación
            application = Application.objects.get(pk=token_obj.application_id)
            
            # Enviar correo de confirmación con PDF adjunto
            from django.core.mail import EmailMultiAlternatives
            import io
            from django.template.loader import get_template
            from xhtml2pdf import pisa
            
            subject = f'ForgeApp: Confirmación de Contrato - {application.name}'
            
            # Renderizar la plantilla HTML del correo
            html_message = render_to_string('forgeapp/email/contract_confirmation_email.html', {
                'client': client,
                'application': application,
                'subscription_type': 'Mensual' if token_obj.subscription_type == 'monthly' else 'Anual',
                'price': token_obj.price,
                'date': timezone.now().strftime('%d/%m/%Y'),
                'site_url': settings.SITE_URL,
                'now': timezone.now()
            })
            
            # Crear versión texto plano del correo
            text_content = f"""
                Estimado/a {client.name},
                
                ¡Gracias por confiar en ForgeApp! Nos complace confirmarle que ha aceptado exitosamente el contrato de servicio para {application.name}.
                
                Adjunto a este correo encontrará una copia completa del contrato firmado en formato PDF. Le recomendamos guardar este documento para futuras referencias.
                
                Detalles del Contrato:
                - Aplicación: {application.name}
                - Tipo de Suscripción: {'Mensual' if token_obj.subscription_type == 'monthly' else 'Anual'}
                - Precio: ${token_obj.price}
                - Fecha: {timezone.now().strftime('%d/%m/%Y')}
                
                Nuestro equipo se pondrá en contacto con usted para coordinar la activación de su suscripción y proporcionarle las instrucciones necesarias para realizar el primer pago. Una vez completado este proceso, tendrá acceso completo a todas las funcionalidades de la aplicación.
                
                En ForgeApp estamos comprometidos con brindarle una experiencia excepcional. Si tiene alguna pregunta, sugerencia o necesita asistencia, nuestro equipo de soporte está siempre disponible para ayudarle.
                
                Le damos la bienvenida a la familia ForgeApp,
                Equipo ForgeApp
                
                ForgeApp - www.forgeapp.cl
                Teléfono: +56 9 1234 5678 | Email: contacto@forgeapp.cl
            """
            
            try:
                # Generar PDF del contrato
                contract_buffer = io.BytesIO()
                
                # Renderizar la plantilla del contrato para el PDF
                contract_template = get_template('forgeapp/pdf/service_contract_pdf.html')
                contract_html = contract_template.render({
                    'client': client,
                    'application': application,
                    'subscription_type': 'Mensual' if token_obj.subscription_type == 'monthly' else 'Anual',
                    'price': token_obj.price,
                    'date': timezone.now().strftime('%d/%m/%Y'),
                    'accept_marketing': client.accept_marketing
                })
                
                # Generar PDF del HTML
                pisa.CreatePDF(
                    contract_html,
                    dest=contract_buffer
                )
                
                # Crear el email con texto alternativo HTML y adjunto
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[client.email]
                )
                
                # Agregar la versión HTML
                email.attach_alternative(html_message, "text/html")
                
                # Adjuntar el PDF
                contract_buffer.seek(0)
                email.attach(f'contrato_{application.name}.pdf', contract_buffer.getvalue(), 'application/pdf')
                
                # Enviar el correo
                email.send(fail_silently=False)
                logger.info(f"Correo de confirmación enviado a {client.email} con contrato adjunto")
                
            except Exception as e:
                logger.error(f"Error al enviar correo de confirmación: {str(e)}")
            
            # Redirigir a la vista de contrato aceptado
            return render(request, 'forgeapp/public_service_contract.html', {
                'is_accepted': True,
                'just_accepted': True,
                'token_obj': token_obj,
                'client': client,
                'application': application,
                'subscription_type': token_obj.subscription_type,
                'token': token
            })
            
        except Exception as e:
            logger.error(f"Error al aceptar contrato: {str(e)}")
            return render(request, 'forgeapp/public_service_contract.html', {
                'is_error': True,
                'error_message': str(e)
            })
    
    # Si no es POST, redirigir a la vista del contrato
    return redirect('forgeapp:view_service_contract', token=token)

# Subscription views
@login_required
def subscription_list(request):
    """Lista de suscripciones"""
    subscriptions = Subscription.objects.all().select_related('client', 'application')
    return render(request, 'forgeapp/subscription_list.html', {'subscriptions': subscriptions})

@login_required
def subscription_detail(request, pk):
    """Detalle de una suscripción"""
    subscription = get_object_or_404(Subscription, pk=pk)
    
    # Pasar la fecha actual para comparaciones en la plantilla
    today = timezone.now().date()
    
    return render(request, 'forgeapp/subscription_detail.html', {
        'subscription': subscription,
        'today': today
    })

@login_required
def subscription_create(request):
    """Crear una nueva suscripción"""
    # Prellenar el formulario si vienen parámetros en la URL
    initial_data = {}
    if request.GET.get('client'):
        initial_data['client'] = request.GET.get('client')
    if request.GET.get('application'):
        initial_data['application'] = request.GET.get('application')
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            
            # Generar ID de referencia si no se ha generado
            if not subscription.reference_id or subscription.reference_id == 'TEMP000000':
                subscription.reference_id = Subscription.generate_reference_id(subscription.payment_type)
                subscription.save()
            
            messages.success(request, 'Suscripción creada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=subscription.pk)
    else:
        form = SubscriptionForm(initial=initial_data)
    
    cancel_url = request.META.get('HTTP_REFERER', 'forgeapp:subscription_list')
    return render(request, 'forgeapp/subscription_form.html', {
        'form': form, 
        'is_create': True,
        'cancel_url': cancel_url
    })

@login_required
def subscription_update(request, pk):
    """Actualizar una suscripción"""
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Suscripción actualizada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=pk)
    else:
        form = SubscriptionForm(instance=subscription)
    
    cancel_url = request.META.get('HTTP_REFERER', f'forgeapp:subscription_detail')
    return render(request, 'forgeapp/subscription_form.html', {
        'form': form, 
        'subscription': subscription, 
        'is_create': False,
        'cancel_url': cancel_url
    })

@login_required
def subscription_delete(request, pk):
    """Eliminar una suscripción"""
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        client_pk = subscription.client.pk  # Guardar el ID del cliente antes de eliminar
        subscription.delete()
        messages.success(request, 'Suscripción eliminada exitosamente.')
        
        # Redirigir a la página de detalle del cliente si venimos de allí
        if 'client_detail' in request.META.get('HTTP_REFERER', ''):
            return redirect('forgeapp:client_detail', pk=client_pk)
        else:
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
        # Verificar que el cliente tenga first_name y last_name
        client = subscription.client
        if not client.first_name or not client.last_name:
            # Dividir el nombre en first_name y last_name si están vacíos
            name_parts = client.name.split()
            if name_parts:
                client.first_name = name_parts[0]
                if len(name_parts) > 1:
                    client.last_name = ' '.join(name_parts[1:])
                client.save()
                logger.info(f"Actualizado first_name y last_name para cliente {client.id}")
        
        # Cambiar estado a activo
        subscription.status = 'active'
        subscription.save()
        logger.info(f"Estado cambiado a 'active' y guardado")
        
        # Actualizar fechas de pago
        subscription.last_payment_date = None  # Asegurar que se considera como primer pago
        subscription.update_payment_dates()
        
        # Crear registros de pago pendiente
        from finance.models import Payment as FinancePayment
        current_date = timezone.now().date()

        if subscription.payment_type == 'annual':
            # Para suscripciones anuales, crear un solo pago
            FinancePayment.objects.create(
                subscription=subscription,
                amount=subscription.price,
                payment_date=None,
                due_date=current_date,
                status='pending',
                notes=f'Pago anual para {current_date.year}'
            )
        else:
            # Para suscripciones mensuales, crear 12 pagos
            for i in range(12):
                # Calcular la fecha para este mes
                if i == 0:
                    payment_date = current_date
                else:
                    if current_date.month + i > 12:
                        new_year = current_date.year + ((current_date.month + i - 1) // 12)
                        new_month = ((current_date.month + i - 1) % 12) + 1
                        payment_date = current_date.replace(year=new_year, month=new_month)
                    else:
                        payment_date = current_date.replace(month=current_date.month + i)

                FinancePayment.objects.create(
                    subscription=subscription,
                    amount=subscription.price,
                    payment_date=None,
                    due_date=payment_date,
                    status='pending',
                    notes=f'Pago mensual para {payment_date.strftime("%B %Y")}'
                )
        
        messages.success(request, 'Suscripción activada exitosamente. Registre el pago manualmente.')
        
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

@login_required
def subscription_renew(request, pk):
    """Genera pagos para el siguiente período (año o 12 meses)"""
    subscription = get_object_or_404(Subscription, pk=pk)
    
    try:
        # Obtener la última fecha de pago o usar la fecha actual
        last_payment = subscription.finance_payments.order_by('-due_date').first()
        start_date = (last_payment.due_date if last_payment else timezone.now().date()) + timezone.timedelta(days=1)
        
        from finance.models import Payment as FinancePayment
        
        if subscription.payment_type == 'annual':
            # Para suscripciones anuales, verificar si ya existe un pago para el siguiente año
            next_year = start_date.year + 1
            existing_payment = FinancePayment.objects.filter(
                subscription=subscription,
                due_date__year=next_year,
                status='pending'
            ).first()
            
            if not existing_payment:
                # Si no existe, crear un pago para el siguiente año
                FinancePayment.objects.create(
                    subscription=subscription,
                    amount=subscription.price,
                    payment_date=None,
                    due_date=start_date.replace(year=next_year),
                    status='pending',
                    notes=f'Pago anual generado automáticamente para {next_year}'
                )
                messages.success(request, f'Pago anual generado para el año {next_year}')
            else:
                messages.info(request, f'Ya existe un pago pendiente para el año {next_year}')
            
        else:  # monthly
            # Para suscripciones mensuales, generar 12 pagos mensuales
            current_date = start_date
            for i in range(12):
                # Calcular la fecha para este mes
                if i == 0:
                    payment_date = current_date
                else:
                    if current_date.month + i > 12:
                        new_year = current_date.year + ((current_date.month + i - 1) // 12)
                        new_month = ((current_date.month + i - 1) % 12) + 1
                        payment_date = current_date.replace(year=new_year, month=new_month)
                    else:
                        payment_date = current_date.replace(month=current_date.month + i)

                FinancePayment.objects.create(
                    subscription=subscription,
                    amount=subscription.price,
                    payment_date=None,
                    due_date=payment_date,
                    status='pending',
                    notes=f'Pago mensual generado automáticamente para {payment_date.strftime("%B %Y")}'
                )
            
            messages.success(request, 'Se generaron los pagos para los próximos 12 meses')
            
    except Exception as e:
        logger.error(f"Error al renovar suscripción: {str(e)}")
        messages.error(request, f'Error al generar los pagos: {str(e)}')
    
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
    
    cancel_url = request.META.get('HTTP_REFERER', 'forgeapp:calculadora_list')
    return render(request, 'forgeapp/calculadora_form.html', {'form': form, 'is_create': True, 'cancel_url': cancel_url})

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
    
    cancel_url = request.META.get('HTTP_REFERER', f'forgeapp:calculadora_detail')
    return render(request, 'forgeapp/calculadora_form.html', {'form': form, 'calculadora': calculadora, 'is_create': False, 'cancel_url': cancel_url})

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
            
            if not calculadora.application:
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
