from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django import forms
from django.db import transaction
from django.http import HttpResponse, FileResponse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from io import BytesIO
import logging
from pdf_generator.views import generar_pdf_recibo_buffer
from .models import Payment, Transaction, Receipt

logger = logging.getLogger('finance')

@login_required
def dashboard(request):
    """Dashboard financiero con KPIs y gráficos"""
    from forgeapp.models import PaymentEvent
    from datetime import date, timedelta

    # Obtener todas las suscripciones y activas
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(status='active')
    active_count = active_subscriptions.count()

    # Calcular MRR (Monthly Recurring Revenue)
    mrr = active_subscriptions.filter(payment_type='monthly').aggregate(
        total=Sum('price')
    )['total'] or 0

    # Calcular cambio en MRR vs mes anterior
    last_month = timezone.now() - timezone.timedelta(days=30)
    mrr_last_month = active_subscriptions.filter(
        payment_type='monthly',
        created_at__lt=last_month
    ).aggregate(total=Sum('price'))['total'] or 0

    if mrr_last_month > 0:
        mrr_change = ((mrr - mrr_last_month) / mrr_last_month) * 100
    else:
        mrr_change = 100 if mrr > 0 else 0

    # Calcular tasa de retención
    total_clients = active_subscriptions.values('client').distinct().count()
    retained_clients = active_subscriptions.filter(
        created_at__lt=last_month
    ).values('client').distinct().count()

    retention_rate = (retained_clients / total_clients * 100) if total_clients > 0 else 0

    # Obtener clientes activos y nuevos
    active_clients = total_clients
    new_clients = active_subscriptions.filter(
        created_at__gte=last_month
    ).values('client').distinct().count()

    # Calcular valor promedio por cliente
    avg_client_value = mrr / active_clients if active_clients > 0 else 0

    # Datos para gráficos - usando PaymentEvent con status='paid'
    monthly_data = []
    monthly_labels = []
    for i in range(6):
        month_start = timezone.now() - timezone.timedelta(days=30 * i)
        month_end = month_start - timezone.timedelta(days=30)
        month_total = PaymentEvent.objects.filter(
            status='paid',
            paid_date__range=[month_end.date(), month_start.date()]
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_data.append(float(month_total))
        monthly_labels.append(month_end.strftime('%B'))

    monthly_data.reverse()
    monthly_labels.reverse()

    # Distribución de pagos
    monthly_count = active_subscriptions.filter(payment_type='monthly').count()
    annual_count = active_subscriptions.filter(payment_type='annual').count()
    payment_distribution = [monthly_count, annual_count]

    # Identificar eventos de pago pendientes (vencidos o próximos)
    today = date.today()

    # Eventos de pago pendientes vencidos o que vencen hoy
    pending_payment_events = PaymentEvent.objects.filter(
        status='pending',
        expected_date__lte=today
    ).select_related('subscription', 'subscription__client', 'subscription__application')

    return render(request, 'finance/dashboard.html', {
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_count,
        'mrr': mrr,
        'mrr_change': mrr_change,
        'retention_rate': round(retention_rate, 1),
        'active_clients': active_clients,
        'new_clients': new_clients,
        'avg_client_value': avg_client_value,
        'monthly_data': monthly_data,
        'monthly_labels': monthly_labels,
        'payment_distribution': payment_distribution,
        'pending_payments': pending_payment_events
    })

@login_required
def payment_list(request):
    """Lista de pagos con filtros"""
    payments = Payment.objects.all()

    # Filtrar por suscripción
    subscription_id = request.GET.get('subscription')
    if subscription_id:
        payments = payments.filter(subscription_id=subscription_id)

    # Filtrar por estado
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)

    # Filtrar por fecha
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        payments = payments.filter(payment_date__range=[start_date, end_date])

    return render(request, 'finance/payment_list.html', {
        'payments': payments.order_by('-payment_date')
    })

@login_required
def payment_detail(request, pk):
    """Detalle de un pago"""
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'finance/payment_detail.html', {
        'payment': payment
    })

@login_required
def payment_mark_completed(request, pk):
    """Marca un pago como completado manualmente"""
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Actualizar pago
                payment.status = 'completed'
                payment.payment_date = timezone.now()
                
                # Actualizar ID de transacción si se proporcionó
                transaction_id = request.POST.get('transaction_id')
                if transaction_id:
                    payment.transaction_id = transaction_id
                
                payment.save()
                
                logger.info(f"Pago {payment.id} marcado como completado manualmente")
                
                # Los signals se encargarán del resto (actualizar suscripción, crear transacción, etc.)
                messages.success(request, 'Pago marcado como completado exitosamente')
        except Exception as e:
            logger.error(f"Error al marcar pago como completado: {str(e)}")
            messages.error(request, f'Error al procesar el pago: {str(e)}')
    
    return redirect('finance:payment_detail', pk=pk)

@login_required
def payment_generate_receipt(request, pk):
    """Genera un recibo para un pago completado"""
    payment = get_object_or_404(Payment, pk=pk)
    
    if payment.status != 'completed':
        messages.error(request, 'Solo se pueden generar recibos para pagos completados')
        return redirect('finance:payment_detail', pk=pk)
    
    try:
        # Verificar si ya existe un recibo
        if hasattr(payment, 'receipt'):
            receipt = payment.receipt
            messages.info(request, 'Este pago ya tiene un recibo generado')
        else:
            # Generar un nuevo recibo
            import secrets
            verification_code = secrets.token_hex(8)
            
            receipt = Receipt.objects.create(
                payment=payment,
                receipt_number=f"REC-{payment.id}-{int(timezone.now().timestamp())}",
                verification_code=verification_code
            )
            
            logger.info(f"Recibo generado para el pago {payment.id}: {receipt.receipt_number}")
            messages.success(request, 'Recibo generado exitosamente')
    
    except Exception as e:
        logger.error(f"Error al generar recibo: {str(e)}")
        messages.error(request, f'Error al generar el recibo: {str(e)}')
    
    return redirect('finance:payment_detail', pk=pk)

@login_required
def receipt_download(request, pk):
    """Descarga un recibo en formato PDF"""
    receipt = get_object_or_404(Receipt, pk=pk)
    payment = receipt.payment
    
    try:
        # Generar el PDF del recibo
        buffer = BytesIO()
        generar_pdf_recibo_buffer(payment, buffer)
        buffer.seek(0)
        
        # Configurar respuesta HTTP
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante_{receipt.receipt_number}.pdf"'
        response.write(buffer.getvalue())
        
        buffer.close()
        logger.info(f"Recibo {receipt.receipt_number} descargado")
        
        return response
    
    except Exception as e:
        logger.error(f"Error al descargar recibo: {str(e)}")
        messages.error(request, f'Error al descargar el recibo: {str(e)}')
        return redirect('finance:payment_detail', pk=payment.pk)

@login_required
def receipt_send(request, pk):
    """Envía un recibo por correo electrónico al cliente"""
    receipt = get_object_or_404(Receipt, pk=pk)
    payment = receipt.payment
    
    if request.method == 'POST':
        try:
            # Verificar que el pago tenga una suscripción y cliente asociados
            if not payment.subscription or not payment.subscription.client:
                messages.error(request, 'El pago no tiene un cliente asociado')
                return redirect('finance:payment_detail', pk=payment.pk)
            
            # Obtener datos para el correo
            client = payment.subscription.client
            application = payment.subscription.application if payment.subscription.application else None
            
            if not client.email:
                messages.error(request, 'El cliente no tiene un correo electrónico configurado')
                return redirect('finance:payment_detail', pk=payment.pk)
            
            # Generar el PDF
            buffer = BytesIO()
            generar_pdf_recibo_buffer(payment, buffer)
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Preparar asunto del correo
            subject = f'ForgeApp: Comprobante de Pago - {application.name if application else "ForgeApp"}'
            
            # Obtener URL del sitio
            site_url = settings.SITE_URL
            
            # Renderizar plantilla de email
            html_content = render_to_string('finance/email/payment_receipt.html', {
                'payment': payment,
                'client': client,
                'subscription': payment.subscription,
                'application': application,
                'site_url': site_url,
                'now': timezone.now()
            })
            
            # Crear el email con texto plano también para mejor compatibilidad
            text_content = f"""
            Estimado/a {client.name},
            
            ¡Su pago ha sido procesado exitosamente!
            
            Nos complace confirmarle que hemos recibido su pago por el servicio de {application.name if application else "ForgeApp"}. Adjunto a este email encontrará el comprobante de pago que puede guardar para sus registros.
            
            Detalles de la transacción:
            - Monto: ${payment.amount}
            - Fecha: {payment.payment_date.strftime('%d/%m/%Y %H:%M') if payment.payment_date else timezone.now().strftime('%d/%m/%Y %H:%M')}
            - Referencia: {payment.subscription.reference_id}
            - Tipo: {payment.subscription.get_payment_type_display()}
            
            Puede verificar la autenticidad de este comprobante escaneando el código QR adjunto en el PDF.
            
            Agradecemos su confianza en nosotros y estamos comprometidos en brindarle el mejor servicio. ¡Su satisfacción es nuestra prioridad!
            
            Si tiene alguna pregunta o necesita asistencia, no dude en contactarnos.
            
            Saludos cordiales,
            Equipo ForgeApp
            www.forgeapp.cl
            """
            
            # Crear mensaje de correo
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[client.email]
            )
            
            # Añadir versión HTML
            email.attach_alternative(html_content, "text/html")
            
            # Adjuntar el PDF
            filename = f"comprobante_{receipt.receipt_number}.pdf"
            email.attach(filename, pdf_data, 'application/pdf')
            
            # Enviar el email
            email.send()
            
            # Actualizar estado de envío
            receipt.sent_to_client = True
            receipt.sent_at = timezone.now()
            receipt.save()
            
            logger.info(f"Recibo {receipt.receipt_number} enviado a {client.email}")
            messages.success(request, f'Recibo enviado exitosamente a {client.email}')
        
        except Exception as e:
            logger.error(f"Error al enviar recibo: {str(e)}")
            messages.error(request, f'Error al enviar el recibo: {str(e)}')
    
    return redirect('finance:payment_detail', pk=payment.pk)

@login_required
def register_subscription_payment(request, subscription_id):
    """
    Registra un pago manual para una suscripción.
    NOTA: Esta función está deprecada. Usa la vista mark_payment_event_paid en forgeapp
    que maneja PaymentEvent en lugar de Payment.
    """
    from forgeapp.models import PaymentEvent
    from datetime import date

    subscription = get_object_or_404(Subscription, pk=subscription_id)

    try:
        with transaction.atomic():
            # Obtener el evento de pago pendiente más antiguo
            payment_event = PaymentEvent.objects.filter(
                subscription=subscription,
                status='pending'
            ).order_by('expected_date').first()

            if not payment_event:
                messages.error(request, 'No hay eventos de pago pendientes para esta suscripción')
                return redirect('forgeapp:subscription_detail', pk=subscription_id)

            # Marcar el evento como pagado
            if payment_event.mark_as_paid(paid_date=date.today()):
                messages.success(request, 'Pago registrado exitosamente')
            else:
                messages.warning(request, 'El evento ya estaba marcado como pagado')

    except Exception as e:
        logger.error(f"Error al registrar pago: {str(e)}")
        messages.error(request, f'Error al registrar el pago: {str(e)}')

    return redirect('forgeapp:subscription_detail', pk=subscription_id)

@login_required
def monthly_report(request):
    """Reporte mensual de ingresos y pagos"""
    from forgeapp.models import PaymentEvent

    # Filtros de fecha
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        # Por defecto, mostrar el mes actual
        today = timezone.now()
        start_date = today.replace(day=1).date()
        end_date = (start_date + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

    # Obtener eventos de pago del período (pagados)
    payment_events = PaymentEvent.objects.filter(
        paid_date__range=[start_date, end_date],
        status='paid'
    ).select_related('subscription__client', 'subscription__application')

    # Calcular totales
    total = payment_events.aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(request, 'finance/reports/monthly.html', {
        'payment_events': payment_events,
        'total': total,
        'start_date': start_date,
        'end_date': end_date,
    })

@login_required
def annual_report(request):
    """Reporte anual con tendencias y comparativas"""
    from forgeapp.models import PaymentEvent

    # Obtener año del reporte
    year = int(request.GET.get('year', timezone.now().year))

    # Calcular totales mensuales
    monthly_totals = []
    total_year = 0

    for month in range(1, 13):
        month_payment_events = PaymentEvent.objects.filter(
            paid_date__year=year,
            paid_date__month=month,
            status='paid'
        )
        month_total = month_payment_events.aggregate(total=Sum('amount'))['total'] or 0
        total_year += month_total

        if month_total > 0:
            monthly_totals.append({
                'month': month,
                'total': month_total
            })

    return render(request, 'finance/reports/annual.html', {
        'year': year,
        'monthly_totals': monthly_totals,
        'total_year': total_year,
    })

@login_required
def cash_flow_report(request):
    """Reporte de flujo de caja con ingresos y egresos"""
    # Filtros de fecha
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        # Por defecto, mostrar el mes actual
        today = timezone.now()
        start_date = today.replace(day=1).date()
        end_date = (start_date + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

    # Obtener transacciones del período
    transactions = Transaction.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('payment', 'payment__subscription')

    # Calcular totales
    income = transactions.filter(type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    expenses = transactions.filter(type='expense').aggregate(
        total=Sum('amount')
    )['total'] or 0

    balance = income - expenses

    return render(request, 'finance/reports/cash_flow.html', {
        'transactions': transactions,
        'income': income,
        'expenses': expenses,
        'balance': balance,
    })

@login_required
def transaction_list(request):
    """Lista de transacciones con filtros y totales"""
    transactions = Transaction.objects.all()

    # Crear formulario de filtros
    class FilterForm(forms.Form):
        type = forms.ChoiceField(
            choices=[('', 'Todos')] + Transaction.TYPE_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'w-full'})
        )
        category = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'class': 'w-full'})
        )
        start_date = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full'})
        )
        end_date = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full'})
        )

    form = FilterForm(request.GET)

    # Aplicar filtros
    if request.GET.get('type'):
        transactions = transactions.filter(type=request.GET['type'])
    
    if request.GET.get('category'):
        transactions = transactions.filter(category__icontains=request.GET['category'])
    
    if request.GET.get('start_date') and request.GET.get('end_date'):
        transactions = transactions.filter(
            date__range=[request.GET['start_date'], request.GET['end_date']]
        )

    # Calcular totales
    total_income = transactions.filter(type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_expenses = transactions.filter(type='expense').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Calcular margen
    margin = total_income - total_expenses
    margin_percentage = (margin / total_income * 100) if total_income > 0 else 0

    return render(request, 'finance/transaction_list.html', {
        'transactions': transactions.order_by('-date'),
        'form': form,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'margin': margin,
        'margin_percentage': margin_percentage
    })

@login_required
def transaction_summary(request):
    """Resumen anual de gastos e ingresos"""
    # Obtener año del reporte (por defecto el año actual)
    year = int(request.GET.get('year', timezone.now().year))
    
    # Preparar datos mensuales
    monthly_data = []
    total_income = 0
    total_expenses = 0
    
    for month in range(1, 13):
        # Obtener transacciones del mes
        month_transactions = Transaction.objects.filter(
            date__year=year,
            date__month=month
        )
        
        # Calcular totales del mes
        month_income = month_transactions.filter(type='income').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        month_expenses = month_transactions.filter(type='expense').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Actualizar totales anuales
        total_income += month_income
        total_expenses += month_expenses
        
        # Agregar datos del mes
        monthly_data.append({
            'month': month,
            'month': month,
            'income': month_income,
            'expenses': month_expenses,
            'balance': month_income - month_expenses
        })

    return render(request, 'finance/transaction_summary.html', {
        'year': year,
        'monthly_data': monthly_data,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_balance': total_income - total_expenses
    })

@login_required
def transaction_detail(request, pk):
    """Detalle de una transacción"""
    transaction = get_object_or_404(Transaction, pk=pk)
    return render(request, 'finance/transaction_detail.html', {
        'transaction': transaction
    })

@login_required
def transaction_create(request):
    """Crear una nueva transacción"""
    if request.method == 'POST':
        type = request.POST.get('type')
        category = request.POST.get('category')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        notes = request.POST.get('notes', '')

        transaction = Transaction.objects.create(
            type=type,
            category=category,
            description=description,
            amount=amount,
            date=date,
            notes=notes
        )

        messages.success(request, 'Transacción creada exitosamente')
        return redirect('finance:transaction_detail', pk=transaction.pk)

    return render(request, 'finance/transaction_form.html', {
        'action': 'Crear',
        'transaction': None
    })

@login_required
def transaction_update(request, pk):
    """Actualizar una transacción existente"""
    transaction = get_object_or_404(Transaction, pk=pk)

    if request.method == 'POST':
        transaction.type = request.POST.get('type')
        transaction.category = request.POST.get('category')
        transaction.description = request.POST.get('description')
        transaction.amount = request.POST.get('amount')
        transaction.date = request.POST.get('date')
        transaction.notes = request.POST.get('notes', '')
        transaction.save()

        messages.success(request, 'Transacción actualizada exitosamente')
        return redirect('finance:transaction_detail', pk=transaction.pk)

    return render(request, 'finance/transaction_form.html', {
        'action': 'Editar',
        'transaction': transaction
    })

@login_required
def transaction_delete(request, pk):
    """Eliminar una transacción"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transacción eliminada exitosamente')
        return redirect('finance:transaction_list')

    return render(request, 'finance/transaction_confirm_delete.html', {
        'transaction': transaction
    })

# Add the missing import for Subscription
from forgeapp.models import Subscription
