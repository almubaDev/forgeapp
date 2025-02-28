from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
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
    return render(request, 'forgeapp/dashboard.html')

# Application views
@login_required
def application_list(request):
    """Lista de aplicaciones"""
    applications = Application.objects.all()
    return render(request, 'forgeapp/application_list.html', {'applications': applications})

@login_required
def application_detail(request, pk):
    """Detalle de una aplicación"""
    application = get_object_or_404(Application, pk=pk)
    return render(request, 'forgeapp/application_detail.html', {'application': application})

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
    return render(request, 'forgeapp/application_form.html', {'form': form})

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
    return render(request, 'forgeapp/application_form.html', {'form': form, 'application': application})

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
    return render(request, 'forgeapp/client_list.html', {'clients': clients})

@login_required
def client_detail(request, pk):
    """Detalle de un cliente"""
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'forgeapp/client_detail.html', {'client': client})

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
    return render(request, 'forgeapp/client_form.html', {'form': form})

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
    return render(request, 'forgeapp/client_form.html', {'form': form, 'client': client})

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
    payments = Payment.objects.filter(subscription__client=client).order_by('-payment_date')
    return render(request, 'forgeapp/client_payment_history.html', {
        'client': client,
        'payments': payments
    })

@login_required
def client_contracts(request, pk):
    """Contratos de un cliente"""
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'forgeapp/client_contracts.html', {'client': client})

@login_required
def view_client_contract(request, pk, token_id):
    """Ver un contrato específico de un cliente"""
    client = get_object_or_404(Client, pk=pk)
    token = get_object_or_404(ServiceContractToken, pk=token_id, client=client)
    return render(request, 'forgeapp/view_client_contract.html', {
        'client': client,
        'token': token
    })

@login_required
def service_contract(request, pk):
    """Generar contrato de servicio"""
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'forgeapp/service_contract.html', {'client': client})

@login_required
def send_service_contract(request, pk):
    """Enviar contrato de servicio por email"""
    client = get_object_or_404(Client, pk=pk)
    messages.success(request, 'Contrato enviado exitosamente.')
    return redirect('forgeapp:client_detail', pk=pk)

def view_service_contract(request, token):
    """Ver contrato de servicio público"""
    token_obj = get_object_or_404(ServiceContractToken, token=token)
    return render(request, 'forgeapp/public_service_contract.html', {'token': token_obj})

def accept_service_contract(request, token):
    """Aceptar contrato de servicio"""
    token_obj = get_object_or_404(ServiceContractToken, token=token)
    if request.method == 'POST':
        token_obj.used = True
        token_obj.used_at = timezone.now()
        token_obj.save()
        messages.success(request, 'Contrato aceptado exitosamente.')
    return redirect('forgeapp:view_service_contract', token=token)

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
        
        # Crear un registro de pago pendiente
        payment = Payment.objects.create(
            subscription=subscription,
            amount=subscription.price,
            payment_date=subscription.next_payment_date or timezone.now().date(),
            status='pending'
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
