from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django import forms
from .models import Payment, Transaction
from forgeapp.models import Subscription

@login_required
def dashboard(request):
    """Dashboard financiero con KPIs y gráficos"""
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

    # Datos para gráficos
    monthly_data = []
    monthly_labels = []
    for i in range(6):
        month_start = timezone.now() - timezone.timedelta(days=30 * i)
        month_end = month_start - timezone.timedelta(days=30)
        month_total = Payment.objects.filter(
            status='completed',
            payment_date__range=[month_end, month_start]
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_data.append(month_total)
        monthly_labels.append(month_end.strftime('%B'))
    
    monthly_data.reverse()
    monthly_labels.reverse()

    # Distribución de pagos
    payment_distribution = [
        active_subscriptions.filter(payment_type='monthly').count(),
        active_subscriptions.filter(payment_type='annual').count()
    ]

    # Identificar suscripciones que necesitan pago
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # Obtener suscripciones activas sin pago este mes
    subscriptions_needing_payment = active_subscriptions.exclude(
        payments__payment_date__gte=start_of_month,
        payments__status='completed'
    )

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
        'pending_payments': subscriptions_needing_payment
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
def register_subscription_payment(request, subscription_id):
    """Registra un pago manual para una suscripción"""
    subscription = get_object_or_404(Subscription, pk=subscription_id)
    
    # Crear el pago
    payment = Payment.objects.create(
        subscription=subscription,
        amount=subscription.price,
        payment_date=timezone.now(),
        due_date=subscription.end_date,
        status='completed',
        notes='Pago registrado manualmente'
    )

    messages.success(request, 'Pago registrado exitosamente')
    return redirect('forgeapp:subscription_detail', pk=subscription_id)

@login_required
def monthly_report(request):
    """Reporte mensual de ingresos y pagos"""
    # Filtros de fecha
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        # Por defecto, mostrar el mes actual
        today = timezone.now()
        start_date = today.replace(day=1).date()
        end_date = (start_date + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
    
    # Obtener pagos del período
    payments = Payment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('subscription__client', 'subscription__application')

    # Calcular totales
    total = payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(request, 'finance/reports/monthly.html', {
        'payments': payments,
        'total': total,
        'start_date': start_date,
        'end_date': end_date,
    })

@login_required
def annual_report(request):
    """Reporte anual con tendencias y comparativas"""
    # Obtener año del reporte
    year = int(request.GET.get('year', timezone.now().year))
    
    # Calcular totales mensuales
    monthly_totals = []
    total_year = 0
    
    for month in range(1, 13):
        month_payments = Payment.objects.filter(
            payment_date__year=year,
            payment_date__month=month,
            status='completed'
        )
        month_total = month_payments.aggregate(total=Sum('amount'))['total'] or 0
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
