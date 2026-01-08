from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime, timedelta, date, time
from django.db import models
from django.http import JsonResponse
import logging
import os
import calendar
from .models import (
    Subscription, Calculadora, ItemCalculo, Payment, PaymentEvent,
    Application, ApplicationConfig, Client, ServiceContractToken, ContactMessage, Appointment
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
    """Procesa el formulario de contacto del landing page con agendamiento"""
    from django.http import JsonResponse

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        msg_content = request.POST.get('message', '').strip()
        appointment_date = request.POST.get('appointment_date', '').strip()
        appointment_time = request.POST.get('appointment_time', '').strip()

        # Validar campos requeridos
        if not name or not email or not msg_content:
            return JsonResponse({'error': 'Por favor complete todos los campos requeridos.'}, status=400)

        if not appointment_date or not appointment_time:
            return JsonResponse({'error': 'Por favor seleccione fecha y hora para la reunión.'}, status=400)

        try:
            # Parsear fecha y hora
            appt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            appt_time = datetime.strptime(appointment_time, '%H:%M').time()
            appt_end_time = (datetime.combine(appt_date, appt_time) + timedelta(minutes=60)).time()

            # Verificar que el slot esté disponible
            if not Appointment.is_slot_available(appt_date, appt_time):
                return JsonResponse({'error': 'El horario seleccionado ya no está disponible. Por favor seleccione otro.'}, status=400)

            # Crear la cita
            appointment = Appointment.objects.create(
                date=appt_date,
                start_time=appt_time,
                end_time=appt_end_time,
                name=name,
                email=email,
                description=msg_content,
                status='scheduled'
            )

            # Crear el mensaje de contacto vinculado a la cita
            ContactMessage.objects.create(
                name=name,
                email=email,
                message=msg_content,
                appointment=appointment
            )

            return JsonResponse({
                'success': True,
                'message': '¡Reunión agendada exitosamente!',
                'appointment': {
                    'date': appointment_date,
                    'time': appointment_time
                }
            })
        except ValueError as e:
            logger.error(f"Error de formato en fecha/hora: {str(e)}")
            return JsonResponse({'error': 'Formato de fecha u hora inválido.'}, status=400)
        except Exception as e:
            logger.error(f"Error al guardar mensaje de contacto: {str(e)}")
            return JsonResponse({'error': 'Hubo un error al procesar tu solicitud.'}, status=500)

    # Si no es POST, redirigir al landing
    return redirect('forgeapp:landing')

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
    contracts = ServiceContractToken.objects.filter(client=client).order_by('-created_at')

    # Actualizar estado de contratos expirados
    for contract in contracts:
        if contract.status == 'pending' and contract.is_expired():
            contract.status = 'expired'
            contract.save()

    # Agregar la aplicación a cada contrato
    for contract in contracts:
        try:
            contract.application = Application.objects.get(pk=contract.application_id)
        except Application.DoesNotExist:
            contract.application = None

    # Contadores para estadísticas
    pending_count = contracts.filter(status='pending').count()
    signed_count = contracts.filter(status='signed').count()
    expired_count = contracts.filter(status='expired').count()

    return render(request, 'forgeapp/client_contracts.html', {
        'client': client,
        'contracts': contracts,
        'pending_count': pending_count,
        'signed_count': signed_count,
        'expired_count': expired_count
    })

@login_required
def delete_contract(request, pk, token_id):
    """Eliminar un contrato con validación de contraseña"""
    from django.contrib.auth import authenticate

    client = get_object_or_404(Client, pk=pk)
    token = get_object_or_404(ServiceContractToken, pk=token_id, client=client)

    if request.method == 'POST':
        password = request.POST.get('password', '')

        # Verificar la contraseña del usuario actual
        user = authenticate(username=request.user.username, password=password)

        if user is not None:
            # Contraseña correcta, eliminar el contrato
            try:
                app_name = "Desconocida"
                try:
                    app = Application.objects.get(pk=token.application_id)
                    app_name = app.name
                except Application.DoesNotExist:
                    pass

                token.delete()

                # Si no quedan contratos aceptados, actualizar el estado del cliente
                remaining_contracts = ServiceContractToken.objects.filter(client=client, used=True).count()
                if remaining_contracts == 0:
                    client.contract_status = 'none'
                    client.save()

                messages.success(request, f'Contrato de "{app_name}" eliminado exitosamente.')
                logger.info(f"Contrato {token_id} eliminado por usuario {request.user.username}")

            except Exception as e:
                logger.error(f"Error al eliminar contrato: {str(e)}")
                messages.error(request, f'Error al eliminar el contrato: {str(e)}')
        else:
            # Contraseña incorrecta
            messages.error(request, 'Contraseña incorrecta. No se pudo eliminar el contrato.')

        return redirect('forgeapp:client_contracts', pk=client.pk)

    # Si no es POST, redirigir a la lista de contratos
    return redirect('forgeapp:client_contracts', pk=client.pk)


@login_required
def download_contract_pdf(request, pk, token_id):
    """Descargar el PDF del contrato firmado"""
    from django.http import FileResponse, Http404

    client = get_object_or_404(Client, pk=pk)
    contract = get_object_or_404(ServiceContractToken, pk=token_id, client=client)

    # Verificar que el contrato esté firmado y tenga PDF
    if contract.status != 'signed' or not contract.signed_pdf:
        messages.error(request, 'Este contrato no tiene un PDF disponible para descargar.')
        return redirect('forgeapp:client_contracts', pk=pk)

    try:
        # Obtener el nombre de la aplicación para el nombre del archivo
        try:
            application = Application.objects.get(pk=contract.application_id)
            app_name = application.name.replace(' ', '_')
        except Application.DoesNotExist:
            app_name = 'App'

        filename = f"Contrato_{client.name.replace(' ', '_')}_{app_name}.pdf"

        response = FileResponse(
            contract.signed_pdf.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Error al descargar PDF del contrato: {str(e)}")
        messages.error(request, 'Error al descargar el PDF del contrato.')
        return redirect('forgeapp:client_contracts', pk=pk)


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
def create_contract(request, pk):
    """Crear contrato de servicio y generar link único con código de autorización"""
    import uuid

    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        # Obtener datos del formulario
        application_id = request.POST.get('application')
        subscription_type = request.POST.get('subscription_type')
        price = request.POST.get('price', '0')
        currency = request.POST.get('currency', 'CLP')

        # Validar datos
        if not application_id or not subscription_type:
            messages.error(request, 'Por favor complete todos los campos.')
            return redirect('forgeapp:service_contract', pk=client.pk)

        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            messages.error(request, 'La aplicación seleccionada no existe.')
            return redirect('forgeapp:service_contract', pk=client.pk)

        # Crear token con expiración de 24 horas
        token = uuid.uuid4().hex
        expires_at = timezone.now() + timezone.timedelta(hours=24)

        # Crear el contrato
        contract = ServiceContractToken.objects.create(
            client=client,
            application_id=application_id,
            subscription_type=subscription_type,
            token=token,
            expires_at=expires_at,
            price=price,
            currency=currency,
            status='pending'
        )

        messages.success(request, f'Contrato creado exitosamente. Código de autorización: {contract.authorization_code}')
        return redirect('forgeapp:client_contracts', pk=client.pk)

    return redirect('forgeapp:service_contract', pk=client.pk)


@login_required
def preview_contract_pdf(request, pk):
    """Descargar contrato de servicio como PDF (vista previa antes de enviar)"""
    from django.http import HttpResponse
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    import io

    client = get_object_or_404(Client, pk=pk)

    # Obtener datos del formulario via GET
    application_id = request.GET.get('application')
    subscription_type = request.GET.get('subscription_type')
    price = request.GET.get('price', '0')
    currency = request.GET.get('currency', 'CLP')

    # Validar datos
    if not application_id or not subscription_type:
        messages.error(request, 'Por favor complete todos los campos antes de descargar.')
        return redirect('forgeapp:service_contract', pk=client.pk)

    try:
        application = Application.objects.get(pk=application_id)
    except Application.DoesNotExist:
        messages.error(request, 'La aplicación seleccionada no existe.')
        return redirect('forgeapp:service_contract', pk=client.pk)

    # Formatear precio según moneda
    try:
        price_int = int(float(price))
        if currency == 'USD':
            formatted_price = f"USD${price_int:,}".replace(",", ",")
        else:
            formatted_price = f"CLP${price_int:,}".replace(",", ".")
    except (ValueError, TypeError):
        formatted_price = f"{currency}$0"

    # Preparar contexto para el PDF
    # Formato de fecha en español
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    now = timezone.now()
    fecha_formateada = f"{now.day} de {meses[now.month - 1]} de {now.year}"

    context = {
        'client': client,
        'application': application,
        'subscription_type': 'Mensual' if subscription_type == 'monthly' else 'Anual',
        'price': price,
        'formatted_price': formatted_price,
        'currency': currency,
        'date': fecha_formateada,
        'accept_marketing': False  # En vista previa no hay aceptación aún
    }

    # Generar PDF
    template = get_template('forgeapp/pdf/service_contract_pdf.html')
    html = template.render(context)

    # Crear el PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)

    if pisa_status.err:
        messages.error(request, 'Error al generar el PDF.')
        return redirect('forgeapp:service_contract', pk=client.pk)

    # Preparar respuesta
    pdf_buffer.seek(0)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')

    # Nombre del archivo
    filename = f"contrato_{application.name}_{client.name}.pdf".replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

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

                # Formato de fecha en español
                meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                         'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
                now = timezone.now()
                fecha_formateada = f"{now.day} de {meses[now.month - 1]} de {now.year}"

                # Renderizar la plantilla del contrato para el PDF
                contract_template = get_template('forgeapp/pdf/service_contract_pdf.html')
                contract_html = contract_template.render({
                    'client': client,
                    'application': application,
                    'subscription_type': 'Mensual' if token_obj.subscription_type == 'monthly' else 'Anual',
                    'price': token_obj.price,
                    'date': fecha_formateada,
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
    """Lista de suscripciones ordenadas con EXPIRED primero"""
    from datetime import date
    from django.db.models import Case, When, Value, IntegerField

    today = date.today()

    # Ordenar con EXPIRED primero usando anotación
    # EXPIRED tiene prioridad 0, los demás tienen prioridad 1
    subscriptions = Subscription.objects.all().select_related('client', 'application').annotate(
        order_priority=Case(
            When(status='expired', then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('order_priority', '-created_at')

    # Agregar flag is_expired calculado dinámicamente para cada suscripción
    for subscription in subscriptions:
        subscription.is_expired_calc = subscription.is_expired

    return render(request, 'forgeapp/subscription_list.html', {
        'subscriptions': subscriptions,
        'today': today
    })

@login_required
def subscription_detail(request, pk):
    """Detalle de una suscripción con eventos de pago"""
    subscription = get_object_or_404(Subscription, pk=pk)

    # Pasar la fecha actual para comparaciones en la plantilla
    today = timezone.now().date()

    # Obtener todos los eventos de pago ordenados por fecha esperada
    payment_events = subscription.payment_events.all().order_by('-expected_date')

    return render(request, 'forgeapp/subscription_detail.html', {
        'subscription': subscription,
        'payment_events': payment_events,
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
            subscription = form.save(commit=False)

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
            subscription = form.save()
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
    """Activa una suscripción y genera el primer evento de pago"""
    subscription = get_object_or_404(Subscription, pk=pk)

    logger.info(f"INICIO: Activando suscripción {subscription.reference_id} (ID: {subscription.id})")
    logger.info(f"Estado actual: {subscription.status}")

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

        # Usar el método activate del modelo
        if subscription.activate():
            messages.success(request, 'Suscripción activada exitosamente. Se generó el primer evento de pago automáticamente.')
        else:
            messages.warning(request, 'La suscripción no está en estado PENDING y no puede ser activada.')

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
    """Cancela una suscripción y elimina eventos pendientes"""
    subscription = get_object_or_404(Subscription, pk=pk)

    if subscription.cancel():
        messages.success(request, 'Suscripción cancelada exitosamente. Se eliminaron todos los eventos de pago pendientes.')
    else:
        messages.warning(request, 'La suscripción ya estaba cancelada.')

    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def subscription_deactivate(request, pk):
    """Desactiva una suscripción y elimina eventos pendientes"""
    subscription = get_object_or_404(Subscription, pk=pk)

    if subscription.deactivate():
        messages.success(request, 'Suscripción desactivada exitosamente. Se eliminaron todos los eventos de pago pendientes.')
    else:
        messages.warning(request, 'La suscripción no está en estado ACTIVE o EXPIRED y no puede ser desactivada.')

    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def subscription_renew(request, pk):
    """Renueva una suscripción INACTIVE o CANCELLED, actualizando start_date y generando nuevo evento"""
    subscription = get_object_or_404(Subscription, pk=pk)

    if subscription.renew():
        messages.success(request, 'Suscripción renovada exitosamente. Se actualizó la fecha de inicio y se generó un nuevo evento de pago.')
    else:
        messages.warning(request, 'La suscripción no está en estado INACTIVE, CANCELLED o EXPIRED y no puede ser renovada.')

    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def mark_payment_event_paid(request, subscription_pk, event_pk):
    """Marca un evento de pago como pagado"""
    from .models import PaymentEvent
    from datetime import date

    subscription = get_object_or_404(Subscription, pk=subscription_pk)
    event = get_object_or_404(PaymentEvent, pk=event_pk, subscription=subscription)

    if event.status == 'paid':
        messages.info(request, 'Este evento de pago ya está marcado como pagado.')
        return redirect('forgeapp:subscription_detail', pk=subscription_pk)

    try:
        # Marcar evento como pagado (esto actualiza la suscripción y genera siguiente evento si auto_renewal=True)
        if event.mark_as_paid(paid_date=date.today()):
            messages.success(request, f'Evento de pago marcado como pagado exitosamente. La suscripción ha sido actualizada.')
        else:
            messages.warning(request, 'El evento ya estaba marcado como pagado.')

    except Exception as e:
        logger.error(f"Error al marcar evento como pagado: {str(e)}")
        messages.error(request, f'Error al marcar el evento como pagado: {str(e)}')

    return redirect('forgeapp:subscription_detail', pk=subscription_pk)

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
    Las suscripciones se crean en estado PENDING sin fecha de inicio.
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
            subscription_type = request.POST.get('subscription_type', 'both')
            auto_renewal = request.POST.get('auto_renewal') == 'on'

            # Usar el método del modelo para generar o actualizar suscripciones
            sub_mensual, sub_anual = calculadora.generar_suscripciones(
                subscription_type=subscription_type,
                auto_renewal=auto_renewal
            )

            # Mensaje de éxito según lo creado
            if subscription_type == 'both':
                messages.success(request, 'Suscripciones mensual y anual creadas en estado PENDIENTE.')
            elif subscription_type == 'monthly':
                messages.success(request, 'Suscripción mensual creada en estado PENDIENTE.')
            elif subscription_type == 'annual':
                messages.success(request, 'Suscripción anual creada en estado PENDIENTE.')

            # Redirigir a la suscripción creada
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


def public_contract(request, token):
    """Vista pública del contrato web para que el cliente firme"""
    try:
        contract = ServiceContractToken.objects.get(token=token)
    except ServiceContractToken.DoesNotExist:
        return render(request, 'forgeapp/public_contract.html', {
            'error': True,
            'error_message': 'El contrato no existe o el enlace es inválido.'
        })

    # Verificar si ha expirado
    if contract.is_expired():
        contract.status = 'expired'
        contract.save()
        return render(request, 'forgeapp/public_contract.html', {
            'error': True,
            'error_message': 'El enlace del contrato ha expirado. Por favor, solicite uno nuevo.'
        })

    # Verificar si ya fue firmado
    if contract.status == 'signed':
        return render(request, 'forgeapp/public_contract.html', {
            'contract': contract,
            'is_signed': True,
            'client': contract.client,
            'application': Application.objects.get(pk=contract.application_id)
        })

    # Obtener datos para mostrar el contrato
    try:
        application = Application.objects.get(pk=contract.application_id)
    except Application.DoesNotExist:
        return render(request, 'forgeapp/public_contract.html', {
            'error': True,
            'error_message': 'La aplicación asociada al contrato no existe.'
        })

    # Formato de fecha en español
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    now = timezone.now()
    fecha_formateada = f"{now.day} de {meses[now.month - 1]} de {now.year}"

    return render(request, 'forgeapp/public_contract.html', {
        'contract': contract,
        'client': contract.client,
        'application': application,
        'subscription_type': 'Mensual' if contract.subscription_type == 'monthly' else 'Anual',
        'price': contract.price,
        'formatted_price': contract.get_formatted_price(),
        'currency': contract.currency,
        'date': fecha_formateada,
        'expires_at': contract.expires_at
    })


def sign_contract(request, token):
    """Procesar la firma del contrato"""
    if request.method != 'POST':
        return redirect('forgeapp:public_contract', token=token)

    try:
        contract = ServiceContractToken.objects.get(token=token)
    except ServiceContractToken.DoesNotExist:
        messages.error(request, 'El contrato no existe.')
        return redirect('forgeapp:public_contract', token=token)

    # Verificar si ha expirado
    if contract.is_expired():
        contract.status = 'expired'
        contract.save()
        messages.error(request, 'El enlace del contrato ha expirado.')
        return redirect('forgeapp:public_contract', token=token)

    # Verificar si ya fue firmado
    if contract.status == 'signed':
        messages.info(request, 'Este contrato ya fue firmado.')
        return redirect('forgeapp:public_contract', token=token)

    # Obtener datos del formulario
    rut = request.POST.get('rut', '').strip()
    nombre = request.POST.get('nombre', '').strip()
    accept_terms = request.POST.get('accept_terms') == 'on'
    authorization_code = request.POST.get('authorization_code', '').strip().upper()

    errors = []

    # Validaciones
    if not rut:
        errors.append('El RUT es requerido.')
    if not nombre:
        errors.append('El nombre completo es requerido.')
    if not accept_terms:
        errors.append('Debe aceptar los términos y condiciones.')
    if not authorization_code:
        errors.append('El código de autorización es requerido.')

    # Validar código de autorización
    if authorization_code and authorization_code != contract.authorization_code:
        errors.append('El código de autorización es incorrecto.')

    if errors:
        for error in errors:
            messages.error(request, error)
        return redirect('forgeapp:public_contract', token=token)

    # Firmar el contrato
    contract.status = 'signed'
    contract.used = True
    contract.used_at = timezone.now()
    contract.signed_rut = rut
    contract.signed_name = nombre
    contract.signed_at = timezone.now()

    # Generar y guardar el PDF del contrato firmado
    try:
        import io
        from django.template.loader import get_template
        from django.core.files.base import ContentFile
        from xhtml2pdf import pisa

        # Obtener la aplicación
        application = Application.objects.get(pk=contract.application_id)
        client = contract.client

        # Formato de fecha en español
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        now = timezone.now()
        fecha_formateada = f"{now.day} de {meses[now.month - 1]} de {now.year}"

        # Formatear precio
        if contract.currency == 'USD':
            formatted_price = f"USD ${contract.price:,.2f}"
        else:
            formatted_price = f"${int(contract.price):,}".replace(',', '.')

        # Renderizar la plantilla del contrato para el PDF
        contract_template = get_template('forgeapp/pdf/service_contract_pdf.html')
        contract_html = contract_template.render({
            'client': client,
            'application': application,
            'subscription_type': 'Mensual' if contract.subscription_type == 'monthly' else 'Anual',
            'price': contract.price,
            'formatted_price': formatted_price,
            'date': fecha_formateada,
            'accept_marketing': client.accept_marketing,
            'signed_name': nombre,
            'signed_rut': rut,
            'signed_at': now
        })

        # Generar PDF del HTML
        pdf_buffer = io.BytesIO()
        pisa.CreatePDF(contract_html, dest=pdf_buffer)

        # Guardar el PDF en el campo del modelo
        pdf_filename = f"contrato_{client.name.replace(' ', '_')}_{application.name.replace(' ', '_')}_{now.strftime('%Y%m%d')}.pdf"
        pdf_buffer.seek(0)
        contract.signed_pdf.save(pdf_filename, ContentFile(pdf_buffer.getvalue()), save=False)

        logger.info(f"PDF del contrato generado y guardado: {pdf_filename}")

    except Exception as e:
        logger.error(f"Error al generar PDF del contrato: {str(e)}")

    contract.save()

    # Actualizar estado del cliente
    contract.client.contract_status = 'accepted'
    contract.client.save()

    messages.success(request, '¡Contrato firmado exitosamente!')
    return redirect('forgeapp:public_contract', token=token)


# Contact Message views
@login_required
def message_list(request):
    """Lista de mensajes de contacto"""
    # Obtener filtro de estado
    status_filter = request.GET.get('status', 'all')

    if status_filter == 'new':
        contact_messages = ContactMessage.objects.filter(status='new')
    elif status_filter == 'read':
        contact_messages = ContactMessage.objects.filter(status='read')
    elif status_filter == 'archived':
        contact_messages = ContactMessage.objects.filter(status='archived')
    else:
        # Por defecto, mostrar solo nuevos y leídos (no archivados)
        contact_messages = ContactMessage.objects.exclude(status='archived')

    # Contadores para las pestañas
    new_count = ContactMessage.objects.filter(status='new').count()
    read_count = ContactMessage.objects.filter(status='read').count()
    archived_count = ContactMessage.objects.filter(status='archived').count()

    return render(request, 'forgeapp/message_list.html', {
        'messages_list': contact_messages,
        'status_filter': status_filter,
        'new_count': new_count,
        'read_count': read_count,
        'archived_count': archived_count
    })


@login_required
def message_detail(request, pk):
    """Detalle de un mensaje de contacto"""
    contact_message = get_object_or_404(ContactMessage, pk=pk)

    # Marcar como leído automáticamente
    contact_message.mark_as_read()

    return render(request, 'forgeapp/message_detail.html', {
        'contact_message': contact_message
    })


@login_required
def message_archive(request, pk):
    """Archivar un mensaje"""
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    contact_message.archive()
    messages.success(request, 'Mensaje archivado exitosamente.')
    return redirect('forgeapp:message_list')


@login_required
def message_unarchive(request, pk):
    """Desarchivar un mensaje"""
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    contact_message.unarchive()
    messages.success(request, 'Mensaje desarchivado exitosamente.')
    return redirect('forgeapp:message_list')


@login_required
def message_delete(request, pk):
    """Eliminar un mensaje"""
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        contact_message.delete()
        messages.success(request, 'Mensaje eliminado exitosamente.')
        return redirect('forgeapp:message_list')
    return render(request, 'forgeapp/message_confirm_delete.html', {
        'contact_message': contact_message
    })


@login_required
def message_update_notes(request, pk):
    """Actualizar notas de un mensaje"""
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        contact_message.notes = notes
        contact_message.save()
        messages.success(request, 'Notas actualizadas exitosamente.')
    return redirect('forgeapp:message_detail', pk=pk)


@login_required
def message_update_meeting_link(request, pk):
    """Actualizar link de reunión de un mensaje"""
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        meeting_link = request.POST.get('meeting_link', '')
        contact_message.meeting_link = meeting_link
        # También actualizar en la cita si existe
        if contact_message.appointment:
            contact_message.appointment.meeting_link = meeting_link
            contact_message.appointment.save()
        contact_message.save()
        messages.success(request, 'Link de reunión actualizado exitosamente.')
    return redirect('forgeapp:message_detail', pk=pk)


# Agenda views
@login_required
def agenda_view(request):
    """Vista principal de la agenda con calendario y vista diaria"""
    # Obtener fecha seleccionada o usar hoy
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    # Obtener mes y año para el mini calendario
    month = int(request.GET.get('month', selected_date.month))
    year = int(request.GET.get('year', selected_date.year))

    # Generar datos del mini calendario
    cal = calendar.Calendar(firstweekday=0)  # Lunes como primer día
    month_days = cal.monthdayscalendar(year, month)

    # Obtener días con citas en el mes
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Días con citas reales (no bloqueados)
    days_with_appointments = set(
        Appointment.objects.filter(
            date__gte=first_day,
            date__lte=last_day,
            status='scheduled',
            is_blocked=False
        ).values_list('date', flat=True)
    )

    # Días con bloqueos manuales
    days_with_blocks = set(
        Appointment.objects.filter(
            date__gte=first_day,
            date__lte=last_day,
            status='scheduled',
            is_blocked=True
        ).values_list('date', flat=True)
    )

    # Generar slots de tiempo para el día seleccionado
    # Orden: 9:00-19:00 (horario laboral), luego 20:00-23:00 (tarde), luego 00:00-08:00 (madrugada)
    # Slots de 1 hora
    time_slots = []
    default_blocked = Appointment.get_default_blocked_slots()

    # Obtener slots habilitados manualmente (status='cancelled' indica habilitación manual)
    manually_enabled = set(
        Appointment.objects.filter(
            date=selected_date,
            status='cancelled',
            is_blocked=False
        ).values_list('start_time', flat=True)
    )

    def add_slot(hour):
        """Helper para agregar un slot a la lista"""
        slot_time = time(hour, 0)
        slot_end = (datetime.combine(selected_date, slot_time) + timedelta(minutes=60)).time()

        # Verificar si hay cita en este slot
        appointment = Appointment.objects.filter(
            date=selected_date,
            start_time=slot_time,
            status='scheduled'
        ).first()

        # Determinar si está bloqueado por defecto
        is_default_blocked = slot_time in default_blocked

        # Verificar si fue habilitado manualmente
        is_manually_enabled = slot_time in manually_enabled

        # Si está bloqueado por defecto pero habilitado manualmente, no es bloqueado
        effective_blocked = is_default_blocked and not is_manually_enabled

        time_slots.append({
            'time': slot_time,
            'time_end': slot_end,
            'time_str': slot_time.strftime('%H:%M'),
            'appointment': appointment,
            'is_default_blocked': effective_blocked,
            'is_manually_enabled': is_manually_enabled,
            'is_available': not appointment and not effective_blocked
        })

    # 1. Primero: Horario laboral (9:00 - 19:00) - slots de 1 hora
    for hour in range(9, 20):
        add_slot(hour)

    # 2. Segundo: Horario tarde/noche (20:00 - 23:00)
    for hour in range(20, 24):
        add_slot(hour)

    # 3. Tercero: Horario madrugada (00:00 - 08:00)
    for hour in range(0, 9):
        add_slot(hour)

    # Navegación del calendario
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    # Nombres de meses en español
    month_names = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

    # Calcular si el día está completamente bloqueado
    # Un día está bloqueado si todos los slots laborales (9:00-19:00) están bloqueados o tienen cita
    available_slots_count = sum(1 for slot in time_slots if slot['is_available'] and not slot['is_default_blocked'])
    is_day_fully_blocked = available_slots_count == 0

    # Contar bloqueos manuales (para saber si hay algo que desbloquear)
    blocked_slots_count = Appointment.objects.filter(
        date=selected_date,
        is_blocked=True,
        status='scheduled'
    ).count()

    context = {
        'selected_date': selected_date,
        'time_slots': time_slots,
        'month_days': month_days,
        'current_month': month,
        'current_year': year,
        'month_name': month_names[month],
        'days_with_appointments': days_with_appointments,
        'days_with_blocks': days_with_blocks,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': date.today(),
        'is_day_fully_blocked': is_day_fully_blocked,
        'blocked_slots_count': blocked_slots_count,
    }

    return render(request, 'forgeapp/agenda.html', context)


@login_required
def appointment_detail(request, pk):
    """Detalle de una cita"""
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, 'forgeapp/appointment_detail.html', {
        'appointment': appointment
    })


@login_required
def appointment_cancel(request, pk):
    """Cancelar una cita"""
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Cita cancelada exitosamente.')
    return redirect('forgeapp:agenda_view')


@login_required
def appointment_complete(request, pk):
    """Marcar cita como completada"""
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.status = 'completed'
        appointment.save()
        messages.success(request, 'Cita marcada como completada.')
    return redirect('forgeapp:agenda_view')


@login_required
def toggle_slot_block(request):
    """Bloquear/desbloquear un slot de tiempo"""
    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        action = request.POST.get('action', 'toggle')

        try:
            slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            slot_time = datetime.strptime(time_str, '%H:%M').time()
            slot_end = (datetime.combine(slot_date, slot_time) + timedelta(minutes=60)).time()

            # Buscar si existe un registro para este slot
            existing = Appointment.objects.filter(
                date=slot_date,
                start_time=slot_time,
                is_blocked=True
            ).first()

            if action == 'enable':
                # Habilitar un horario bloqueado por defecto (crear slot disponible especial)
                if not existing:
                    Appointment.objects.create(
                        date=slot_date,
                        start_time=slot_time,
                        end_time=slot_end,
                        name='Habilitado manualmente',
                        email='',
                        is_blocked=False,
                        status='cancelled'  # Status especial para indicar slot habilitado
                    )
                return JsonResponse({'status': 'enabled'})

            elif action == 'block':
                # Bloquear un slot disponible
                if not existing:
                    Appointment.objects.create(
                        date=slot_date,
                        start_time=slot_time,
                        end_time=slot_end,
                        name='Bloqueado',
                        email='',
                        is_blocked=True,
                        status='scheduled'
                    )
                return JsonResponse({'status': 'blocked'})

            elif action == 'unblock':
                # Desbloquear un slot bloqueado manualmente
                if existing:
                    existing.delete()
                return JsonResponse({'status': 'unblocked'})

            else:
                # Toggle por defecto
                if existing:
                    existing.delete()
                    return JsonResponse({'status': 'unblocked'})
                else:
                    Appointment.objects.create(
                        date=slot_date,
                        start_time=slot_time,
                        end_time=slot_end,
                        name='Bloqueado',
                        email='',
                        is_blocked=True,
                        status='scheduled'
                    )
                    return JsonResponse({'status': 'blocked'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def block_full_day(request):
    """Bloquear todos los horarios disponibles de un día completo"""
    if request.method == 'POST':
        date_str = request.POST.get('date')

        try:
            slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            blocked_count = 0

            # Horarios laborales: 9:00 a 19:00 (los que están disponibles por defecto) - slots de 1 hora
            for hour in range(9, 20):
                slot_time = time(hour, 0)
                slot_end = (datetime.combine(slot_date, slot_time) + timedelta(minutes=60)).time()

                # Verificar si ya hay algo en este slot
                existing = Appointment.objects.filter(
                    date=slot_date,
                    start_time=slot_time,
                    status='scheduled'
                ).first()

                # Solo bloquear si no hay cita o bloqueo existente
                if not existing:
                    Appointment.objects.create(
                        date=slot_date,
                        start_time=slot_time,
                        end_time=slot_end,
                        name='Bloqueado',
                        email='',
                        is_blocked=True,
                        status='scheduled'
                    )
                    blocked_count += 1

            return JsonResponse({
                'success': True,
                'blocked_count': blocked_count,
                'message': f'Se bloquearon {blocked_count} horarios'
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def unblock_full_day(request):
    """Desbloquear todos los horarios bloqueados de un día completo"""
    if request.method == 'POST':
        date_str = request.POST.get('date')

        try:
            slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Eliminar todos los bloqueos manuales del día (is_blocked=True)
            deleted_count, _ = Appointment.objects.filter(
                date=slot_date,
                is_blocked=True,
                status='scheduled'
            ).delete()

            return JsonResponse({
                'success': True,
                'unblocked_count': deleted_count,
                'message': f'Se desbloquearon {deleted_count} horarios'
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def get_available_slots(request):
    """API para obtener slots disponibles para una fecha (público)"""
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Fecha requerida'}, status=400)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)

    # No permitir fechas pasadas
    if selected_date < date.today():
        return JsonResponse({'slots': [], 'message': 'No se pueden agendar citas en fechas pasadas'})

    # Generar slots disponibles (horario laboral: 9:00 - 19:00)
    # Slots de 1 hora, el último slot es 19:00 que termina a las 20:00
    available_slots = []

    for hour in range(9, 20):
        slot_time = time(hour, 0)

        # Verificar si está disponible
        if Appointment.is_slot_available(selected_date, slot_time):
            available_slots.append({
                'time': slot_time.strftime('%H:%M'),
                'display': f"{slot_time.strftime('%H:%M')} - {(datetime.combine(selected_date, slot_time) + timedelta(minutes=60)).strftime('%H:%M')}"
            })

    return JsonResponse({'slots': available_slots, 'date': date_str})
