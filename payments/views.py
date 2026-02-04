"""
Vistas de testing para integraciones de pago.
Solo accesibles para superusuarios.
"""

import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .providers.flow import PaymentService, CustomerService, SubscriptionService, RefundService
from .exceptions import FlowException


def is_superuser(user):
    """Verifica si el usuario es superusuario."""
    return user.is_superuser


def get_flow_env():
    """Retorna informacion del entorno de Flow."""
    api_url = getattr(settings, 'FLOW_API_URL', '')
    return {
        'api_url': api_url,
        'is_sandbox': 'sandbox' in api_url,
    }


def is_flow_configured():
    """Verifica si Flow esta configurado."""
    return all([
        getattr(settings, 'FLOW_API_URL', None),
        getattr(settings, 'FLOW_API_KEY', None),
        getattr(settings, 'FLOW_SECRET_KEY', None),
    ])


# =====================
# TEST INDEX (PRINCIPAL - SELECTOR DE PROVEEDORES)
# =====================

@login_required
@user_passes_test(is_superuser)
def test_index(request):
    """Pagina principal del test suite - selector de proveedores."""
    return render(request, 'payments/test_index.html', {
        'flow_configured': is_flow_configured(),
    })


# =====================
# FLOW TEST INDEX
# =====================

@login_required
@user_passes_test(is_superuser)
def flow_test_index(request):
    """Pagina principal del test suite de Flow."""
    return render(request, 'payments/flow/test_index.html', {
        'flow_env': get_flow_env(),
    })


# =====================
# FLOW: PAYMENT TEST
# =====================

@login_required
@user_passes_test(is_superuser)
def flow_test_payment(request):
    """Vista de testing para PaymentService de Flow."""
    # Obtener historial de sesion
    test_history = request.session.get('payment_test_history', [])

    context = {
        'test_history': test_history,
        'status_result': None,
        'flow_env': get_flow_env(),
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        try:
            payment_service = PaymentService()

            if action == 'create_payment':
                commerce_order = f"TEST-{uuid.uuid4().hex[:8].upper()}"
                amount = int(request.POST.get('amount', 1000))
                email = request.POST.get('email', 'test@ejemplo.com')
                subject = request.POST.get('subject', 'Pago de prueba')

                result = payment_service.create(
                    commerce_order=commerce_order,
                    subject=subject,
                    amount=amount,
                    email=email,
                    url_confirmation=f"{settings.SITE_URL}/payments/confirm/",
                    url_return=f"{settings.SITE_URL}/payments/return/",
                )

                # Agregar al historial
                test_history.insert(0, {
                    'commerce_order': commerce_order,
                    'amount': amount,
                    'email': email,
                    'subject': subject,
                    'url': result['url'],
                    'token': result['token'],
                    'flow_order': result['flow_order'],
                    'status': None,  # Pendiente de verificar
                })

                # Limitar historial a 20 items
                test_history = test_history[:20]
                request.session['payment_test_history'] = test_history

                messages.success(request, f'Pago creado: {commerce_order}')

            elif action == 'check_status':
                token = request.POST.get('token', '').strip()

                if token:
                    status = payment_service.get_status(token)
                    context['status_result'] = {
                        'raw': status,
                        'status_code': status.get('status'),
                        'status_label': PaymentService.get_status_label(status.get('status', 0)),
                        'is_paid': PaymentService.is_paid(status.get('status', 0)),
                    }

                    # Actualizar estado en historial si existe
                    for item in test_history:
                        if item['token'] == token:
                            item['status'] = status.get('status')
                            break
                    request.session['payment_test_history'] = test_history

                else:
                    messages.warning(request, 'Ingresa un token para verificar')

            elif action == 'clear_history':
                request.session['payment_test_history'] = []
                test_history = []
                messages.success(request, 'Historial limpiado')

        except FlowException as e:
            messages.error(request, f'Error de Flow: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context['test_history'] = test_history
    return render(request, 'payments/flow/test_payment.html', context)


# =====================
# FLOW: CUSTOMER TEST
# =====================

@login_required
@user_passes_test(is_superuser)
def flow_test_customer(request):
    """Vista de testing para CustomerService de Flow."""
    test_history = request.session.get('customer_test_history', [])

    context = {
        'test_history': test_history,
        'flow_env': get_flow_env(),
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        try:
            customer_service = CustomerService()

            if action == 'create_customer':
                external_id = f"CLI-{uuid.uuid4().hex[:8].upper()}"
                name = request.POST.get('name', 'Cliente de Prueba')
                email = request.POST.get('email', 'test@ejemplo.com')

                result = customer_service.create(
                    name=name,
                    email=email,
                    external_id=external_id,
                )

                test_history.insert(0, {
                    'type': 'customer',
                    'external_id': external_id,
                    'customer_id': result.get('customerId'),
                    'name': name,
                    'email': email,
                    'has_card': False,
                    'register_url': None,
                    'register_token': None,
                })

                test_history = test_history[:20]
                request.session['customer_test_history'] = test_history
                messages.success(request, f'Cliente creado: {result.get("customerId")}')

            elif action == 'register_card':
                customer_id = request.POST.get('customer_id', '').strip()

                if customer_id:
                    result = customer_service.register(
                        customer_id=customer_id,
                        url_return=f"{settings.SITE_URL}/payments/customer/register-return/",
                    )

                    # Mostrar resultado inmediatamente
                    context['register_result'] = {
                        'url': result['url'],
                        'token': result['token'],
                        'customer_id': customer_id,
                    }

                    # Actualizar historial
                    for item in test_history:
                        if item.get('customer_id') == customer_id:
                            item['register_url'] = result['url']
                            item['register_token'] = result['token']
                            break
                    request.session['customer_test_history'] = test_history

                    messages.success(request, 'URL de registro generada')
                else:
                    messages.warning(request, 'Ingresa un Customer ID')

            elif action == 'check_register':
                token = request.POST.get('register_token', '').strip()

                if token:
                    result = customer_service.get_register_status(token)
                    context['register_status'] = result

                    # Actualizar estado en historial
                    for item in test_history:
                        if item.get('register_token') == token:
                            item['has_card'] = result.get('status') == 1
                            break
                    request.session['customer_test_history'] = test_history
                else:
                    messages.warning(request, 'Ingresa un token de registro')

            elif action == 'charge':
                customer_id = request.POST.get('customer_id', '').strip()
                amount = int(request.POST.get('charge_amount', 1000))
                subject = request.POST.get('charge_subject', 'Cargo de prueba')

                if customer_id:
                    commerce_order = f"CHARGE-{uuid.uuid4().hex[:8].upper()}"
                    result = customer_service.charge(
                        customer_id=customer_id,
                        amount=amount,
                        subject=subject,
                        commerce_order=commerce_order,
                    )
                    context['charge_result'] = result
                    messages.success(request, f'Cargo realizado: {commerce_order}')
                else:
                    messages.warning(request, 'Ingresa un Customer ID')

            elif action == 'clear_history':
                request.session['customer_test_history'] = []
                test_history = []
                messages.success(request, 'Historial limpiado')

        except FlowException as e:
            messages.error(request, f'Error de Flow: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context['test_history'] = test_history
    return render(request, 'payments/flow/test_customer.html', context)


# =====================
# FLOW: SUBSCRIPTION TEST
# =====================

@login_required
@user_passes_test(is_superuser)
def flow_test_subscription(request):
    """Vista de testing para SubscriptionService de Flow."""
    plans_history = request.session.get('plans_test_history', [])
    subs_history = request.session.get('subs_test_history', [])

    context = {
        'plans_history': plans_history,
        'subs_history': subs_history,
        'flow_env': get_flow_env(),
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        try:
            subscription_service = SubscriptionService()

            if action == 'create_plan':
                plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
                name = request.POST.get('plan_name', 'Plan de Prueba')
                amount = int(request.POST.get('plan_amount', 10000))
                interval = int(request.POST.get('plan_interval', 3))

                result = subscription_service.create_plan(
                    plan_id=plan_id,
                    name=name,
                    amount=amount,
                    interval=interval,
                )

                plans_history.insert(0, {
                    'plan_id': plan_id,
                    'name': name,
                    'amount': amount,
                    'interval': interval,
                    'interval_label': SubscriptionService.get_interval_label(interval),
                })

                plans_history = plans_history[:10]
                request.session['plans_test_history'] = plans_history
                messages.success(request, f'Plan creado: {plan_id}')

            elif action == 'create_subscription':
                plan_id = request.POST.get('sub_plan_id', '').strip()
                customer_id = request.POST.get('sub_customer_id', '').strip()

                if plan_id and customer_id:
                    result = subscription_service.create(
                        plan_id=plan_id,
                        customer_id=customer_id,
                        url_return=f"{settings.SITE_URL}/payments/subscription/return/",
                    )

                    subs_history.insert(0, {
                        'subscription_id': result.get('subscription_id'),
                        'plan_id': plan_id,
                        'customer_id': customer_id,
                        'url': result['url'],
                        'token': result['token'],
                    })

                    subs_history = subs_history[:10]
                    request.session['subs_test_history'] = subs_history
                    messages.success(request, 'Suscripcion creada')
                else:
                    messages.warning(request, 'Ingresa Plan ID y Customer ID')

            elif action == 'check_subscription':
                subscription_id = request.POST.get('subscription_id', '').strip()

                if subscription_id:
                    result = subscription_service.get(subscription_id)
                    context['subscription_status'] = {
                        'raw': result,
                        'status': result.get('status'),
                        'status_label': 'Activa' if result.get('status') == 1 else 'Cancelada' if result.get('status') == 2 else 'Suspendida',
                        'plan_id': result.get('planId'),
                        'next_invoice': result.get('next_invoice_date'),
                    }

                    # Actualizar estado en historial
                    for item in subs_history:
                        if item.get('subscription_id') == subscription_id:
                            item['status'] = result.get('status')
                            break
                    request.session['subs_test_history'] = subs_history
                else:
                    messages.warning(request, 'Subscription ID no válido')

            elif action == 'clear_history':
                request.session['plans_test_history'] = []
                request.session['subs_test_history'] = []
                plans_history = []
                subs_history = []
                messages.success(request, 'Historial limpiado')

        except FlowException as e:
            messages.error(request, f'Error de Flow: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context['plans_history'] = plans_history
    context['subs_history'] = subs_history
    return render(request, 'payments/flow/test_subscription.html', context)


# =====================
# FLOW: REFUND TEST
# =====================

@login_required
@user_passes_test(is_superuser)
def flow_test_refund(request):
    """Vista de testing para RefundService de Flow."""
    test_history = request.session.get('refund_test_history', [])

    context = {
        'test_history': test_history,
        'flow_env': get_flow_env(),
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        try:
            refund_service = RefundService()

            if action == 'create_refund':
                flow_order = int(request.POST.get('flow_order', 0))
                amount = int(request.POST.get('amount', 1000))
                receiver_email = request.POST.get('receiver_email', 'test@ejemplo.com')

                if flow_order:
                    result = refund_service.create(
                        flow_order=flow_order,
                        amount=amount,
                        receiver_email=receiver_email,
                    )

                    test_history.insert(0, {
                        'flow_order': flow_order,
                        'amount': amount,
                        'receiver_email': receiver_email,
                        'token': result.get('token'),
                        'status': result.get('status'),
                    })

                    test_history = test_history[:20]
                    request.session['refund_test_history'] = test_history
                    messages.success(request, 'Reembolso creado')
                else:
                    messages.warning(request, 'Ingresa un Flow Order valido')

            elif action == 'check_status':
                token = request.POST.get('token', '').strip()

                if token:
                    result = refund_service.get_status(token)
                    context['status_result'] = {
                        'raw': result,
                        'status_code': result.get('status'),
                        'status_label': RefundService.get_status_label(result.get('status', 0)),
                    }

                    # Actualizar estado en historial
                    for item in test_history:
                        if item.get('token') == token:
                            item['status'] = result.get('status')
                            break
                    request.session['refund_test_history'] = test_history
                else:
                    messages.warning(request, 'Ingresa un token')

            elif action == 'clear_history':
                request.session['refund_test_history'] = []
                test_history = []
                messages.success(request, 'Historial limpiado')

        except FlowException as e:
            messages.error(request, f'Error de Flow: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context['test_history'] = test_history
    return render(request, 'payments/flow/test_refund.html', context)


# =====================
# FLOW: WEBHOOKS Y RETORNO
# =====================

@csrf_exempt
@require_POST
def payment_confirm(request):
    """Webhook de confirmacion de pago."""
    token = request.POST.get('token')

    if not token:
        return HttpResponse(status=400)

    try:
        payment_service = PaymentService()
        status = payment_service.get_status(token)
        # Aqui procesar el pago segun el estado
        return HttpResponse(status=200)
    except Exception:
        return HttpResponse(status=500)


def payment_return(request):
    """Vista de retorno despues de un pago."""
    token = request.GET.get('token', '')
    status_info = None
    error = None

    if token:
        try:
            payment_service = PaymentService()
            status = payment_service.get_status(token)
            status_info = {
                'status_code': status.get('status'),
                'status_label': PaymentService.get_status_label(status.get('status', 0)),
                'is_paid': PaymentService.is_paid(status.get('status', 0)),
                'commerce_order': status.get('commerceOrder'),
                'amount': status.get('amount'),
            }
        except Exception as e:
            error = str(e)

    return render(request, 'payments/payment_return.html', {
        'token': token,
        'status_info': status_info,
        'error': error,
    })


def customer_register_return(request):
    """Vista de retorno despues de registrar tarjeta."""
    token = request.GET.get('token', '')
    status_info = None
    error = None

    if token:
        try:
            customer_service = CustomerService()
            status = customer_service.get_register_status(token)
            status_info = {
                'status': status.get('status'),
                'is_registered': status.get('status') == 1,
                'customer_id': status.get('customerId'),
            }
        except Exception as e:
            error = str(e)

    return render(request, 'payments/customer_register_return.html', {
        'token': token,
        'status_info': status_info,
        'error': error,
    })


def subscription_return(request):
    """Vista de retorno despues de suscribirse."""
    token = request.GET.get('token', '')
    return render(request, 'payments/subscription_return.html', {
        'token': token,
    })
