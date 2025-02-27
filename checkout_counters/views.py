# checkout_counters/views.py
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from .models import PaymentLink, Receipt
import uuid
from datetime import datetime, timedelta
import mercadopago
import json
import logging
import base64
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class PaymentLinkListView(LoginRequiredMixin, ListView):
    model = PaymentLink
    template_name = 'checkout_counters/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_amount'] = sum(payment.amount for payment in self.get_queryset().filter(status='paid'))
        context['pending_amount'] = sum(payment.amount for payment in self.get_queryset().filter(status='pending'))
        return context

class PaymentLinkCreateView(LoginRequiredMixin, CreateView):
    model = PaymentLink
    fields = ['subscription', 'amount', 'description']
    template_name = 'checkout_counters/payment_form.html'
    success_url = reverse_lazy('checkout_counters:payment_list')

    def form_valid(self, form):
        form.instance.reference_id = str(uuid.uuid4())
        form.instance.expires_at = datetime.now() + timedelta(days=7)

        # Validar que la suscripción existe
        if not form.instance.subscription:
            form.add_error('subscription', 'La suscripción es requerida')
            return self.form_invalid(form)
        
        # Configurar SDK de Mercado Pago
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        
        # Crear preferencia de pago
        # Construir URLs usando SITE_URL en lugar de request.build_absolute_uri
        base_url = settings.SITE_URL.rstrip('/')
        payment_return_url = f"{base_url}{reverse('checkout_counters:payment_return')}"
        
        # Obtener información del cliente desde la suscripción
        client = form.instance.subscription.client
        
        # Asignar datos del cliente al PaymentLink
        form.instance.payer_email = client.email
        form.instance.payer_first_name = client.first_name
        form.instance.payer_last_name = client.last_name
        
        preference_data = {
            "items": [
                {
                    "title": form.instance.description,
                    "quantity": 1,
                    "currency_id": "CLP",  # Moneda Chilena
                    "unit_price": float(form.instance.amount),
                    "description": f"Pago de suscripción {form.instance.subscription.reference_id}",
                    "category_id": "subscriptions",
                    "id": form.instance.reference_id
                }
            ],
            "external_reference": form.instance.reference_id,
            "expires": True,
            "expiration_date_to": form.instance.expires_at.isoformat(),
            "back_urls": {
                "success": payment_return_url,
                "failure": payment_return_url,
                "pending": payment_return_url
            },
            "auto_return": "approved",
            "notification_url": settings.MP_WEBHOOK_URL,
            "payer": {
                "email": client.email,
                "first_name": client.first_name,
                "last_name": client.last_name
            }
        }
        
        logger.info(f"URLs configuradas para Mercado Pago:")
        logger.info(f"Success URL: {payment_return_url}")
        logger.info(f"Notification URL: {settings.MP_WEBHOOK_URL}")
        
        # Log detallado de los datos enviados a MercadoPago
        logger.info(f"DATOS COMPLETOS ENVIADOS A MERCADOPAGO: {json.dumps(preference_data, indent=2)}")
        
        # Crear preferencia en Mercado Pago
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            # Guardar link de pago
            logger.info(f"Preference response: {preference_response}")
            form.instance.payment_link = preference_response["response"]["init_point"]
            messages.success(self.request, 'Link de pago creado exitosamente')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Error al crear el link de pago')
            return self.form_invalid(form)

class PaymentLinkDetailView(LoginRequiredMixin, DetailView):
    model = PaymentLink
    template_name = 'checkout_counters/payment_detail.html'
    context_object_name = 'payment'

    def get_object(self, queryset=None):
        """
        Retorna el objeto basado en pk o reference_id
        """
        if queryset is None:
            queryset = self.get_queryset()

        # Intentar obtener por pk primero
        pk = self.kwargs.get('pk')
        if pk is not None:
            queryset = queryset.filter(pk=pk)
        else:
            # Si no hay pk, usar reference_id
            reference_id = self.kwargs.get('reference_id')
            if reference_id is None:
                raise AttributeError("Se requiere pk o reference_id")
            queryset = queryset.filter(reference_id=reference_id)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404("No se encontró el pago")
        return obj

class PaymentLinkDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = PaymentLink
    template_name = 'checkout_counters/payment_confirm_delete.html'
    success_url = reverse_lazy('checkout_counters:payment_list')
    success_message = "Link de pago eliminado exitosamente"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

class PaymentLinkUpdateView(LoginRequiredMixin, UpdateView):
    model = PaymentLink
    fields = ['status', 'payer_email', 'payer_first_name', 'payer_last_name']
    template_name = 'checkout_counters/payment_form.html'

    def get_success_url(self):
        return reverse('checkout_counters:payment_detail', kwargs={'pk': self.object.pk})
        
    def form_valid(self, form):
        # Actualizar el campo payer_name para mantener compatibilidad
        form.instance.payer_name = f"{form.instance.payer_first_name or ''} {form.instance.payer_last_name or ''}".strip()
        return super().form_valid(form)

@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    try:
        logger.info("Webhook de Mercado Pago recibido")
        logger.info(f"Request body: {request.body.decode()}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        data = json.loads(request.body)
        logger.info(f"Webhook data: {data}")
        
        if data.get("type") == "payment":
            logger.info(f"Procesando notificación de pago {data['data']['id']}")
            
            # Verificar que el token de acceso esté configurado
            if not settings.MP_ACCESS_TOKEN:
                error_msg = "Token de acceso de Mercado Pago no configurado"
                logger.error(error_msg)
                return HttpResponse(status=500)
            
            # Configurar SDK de Mercado Pago
            sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            
            try:
                # Obtener información del pago
                payment_info = sdk.payment().get(data["data"]["id"])
                logger.info(f"Información del pago: {payment_info}")
                
                if payment_info["status"] == 200:
                    payment_data = payment_info["response"]
                    external_reference = payment_data.get("external_reference")
                    
                    if external_reference:
                        # Usar el manager para actualizar el estado
                        payment_link = PaymentLink.objects.update_payment_status(
                            reference_id=external_reference,
                            status=payment_data["status"],
                            payment_data=payment_data
                        )
                        
                        if payment_link:
                            # Procesar pago aprobado
                            if payment_link.is_paid:
                                from .utils import process_successful_payment
                                if process_successful_payment(payment_link):
                                    logger.info(f"Pago procesado exitosamente: {external_reference}")
                                else:
                                    logger.error(f"Error al procesar el pago: {external_reference}")
                                    return HttpResponse(status=500)
                            else:
                                logger.info(f"Pago no aprobado: {external_reference}, status: {payment_data['status']}")
                        else:
                            logger.error(f"No se pudo actualizar el estado del pago: {external_reference}")
                        
                    else:
                        logger.error(f"Payment {data['data']['id']} has no external reference")
                        return HttpResponse(status=400)
                
                else:
                    logger.error(f"Error getting payment info: {payment_info}")
                    return HttpResponse(status=500)
            
            except Exception as mp_error:
                logger.error(f"Error al obtener información del pago: {str(mp_error)}")
                return HttpResponse(status=500)
        
        return HttpResponse(status=200)
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding webhook JSON: {str(e)}")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return HttpResponse(status=500)

def check_payment_status(request, reference_id):
    try:
        payment_link = get_object_or_404(PaymentLink, reference_id=reference_id)
        
        # Configurar SDK de Mercado Pago
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        
        # Buscar pagos por referencia externa
        search_result = sdk.payment().search({
            "external_reference": reference_id
        })
        
        if search_result["status"] == 200 and search_result["response"]["results"]:
            # Tomar el pago más reciente
            payment_data = search_result["response"]["results"][0]
            
            # Usar el manager para actualizar el estado
            payment_link = PaymentLink.objects.update_payment_status(
                reference_id=reference_id,
                status=payment_data["status"],
                payment_data=payment_data
            )
            
            if not payment_link:
                logger.error(f"No se pudo actualizar el estado del pago: {reference_id}")
                messages.error(request, "Error al verificar el estado del pago")
                return redirect('checkout_counters:payment_list')
            
            if payment_link.is_paid:
                from .utils import process_successful_payment
                if process_successful_payment(payment_link, request):
                    messages.success(request, "El pago ha sido confirmado")
                else:
                    messages.error(request, "Error al procesar el comprobante")
            elif payment_link.status == "pending":
                messages.warning(request, "El pago aún está pendiente")
            else:
                messages.error(request, "El pago fue rechazado o cancelado")
        else:
            messages.info(request, "No se encontraron pagos asociados")
        
        return redirect('checkout_counters:payment_result', reference_id=reference_id)
        
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        messages.error(request, "Error al verificar el estado del pago")
        return redirect('checkout_counters:payment_list')

def update_pending_payments(request):
    try:
        # Obtener todos los pagos pendientes
        pending_payments = PaymentLink.objects.filter(status='pending')
        
        total_pending = pending_payments.count()
        if total_pending == 0:
            messages.warning(request, "No hay pagos pendientes para actualizar")
            return redirect('checkout_counters:payment_list')
        
        messages.info(request, f"Verificando {total_pending} pagos pendientes...")
        
        # Configurar SDK de Mercado Pago
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        
        updated_count = 0
        paid_count = 0
        
        for payment in pending_payments:
            try:
                # Buscar pagos por referencia externa
                search_result = sdk.payment().search({
                    "external_reference": payment.reference_id
                })
                
                if search_result["status"] == 200 and search_result["response"]["results"]:
                    # Tomar el pago más reciente
                    payment_data = search_result["response"]["results"][0]
                    
                    # Usar el manager para actualizar el estado
                    updated_payment = PaymentLink.objects.update_payment_status(
                        reference_id=payment.reference_id,
                        status=payment_data["status"],
                        payment_data=payment_data
                    )
                    
                    if updated_payment:
                        updated_count += 1
                        if updated_payment.is_paid:
                            from .utils import process_successful_payment
                            if process_successful_payment(updated_payment):
                                paid_count += 1
                    else:
                        logger.error(f"No se pudo actualizar el estado del pago: {payment.reference_id}")
            
            except Exception as e:
                logger.error(f"Error checking payment {payment.reference_id}: {str(e)}")
                continue
        
        if updated_count > 0:
            messages.success(
                request,
                f"Se actualizaron {updated_count} pagos ({paid_count} confirmados)"
            )
        else:
            messages.info(request, f"No se encontraron cambios en los {total_pending} pagos pendientes")
        
    except Exception as e:
        logger.error(f"Error updating pending payments: {str(e)}")
        messages.error(request, "Error al actualizar los pagos pendientes")
    
    return redirect('checkout_counters:payment_list')

def payment_result(request, reference_id):
    """Vista para mostrar el resultado del pago"""
    payment_link = get_object_or_404(PaymentLink, reference_id=reference_id)
    return render(request, 'checkout_counters/payment_result.html', {
        'payment': payment_link
    })

def verify_receipt(request, secret_code):
    """Vista para verificar la autenticidad de un comprobante usando el código secreto (UUID)"""
    try:
        receipt = Receipt.objects.select_related('payment_link').get(secret_code=secret_code)
        is_valid = True
    except Receipt.DoesNotExist:
        receipt = None
        is_valid = False

    return render(request, 'checkout_counters/verify_receipt.html', {
        'receipt': receipt,
        'is_valid': is_valid
    })

def verify_code_form(request):
    """Vista para mostrar el formulario de verificación de código"""
    from .forms import VerificationCodeForm
    
    form = VerificationCodeForm()
    
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            return redirect('checkout_counters:verify_code_result', verification_code=verification_code)
    
    return render(request, 'checkout_counters/verify_code_form.html', {
        'form': form
    })

def verify_code_result(request, verification_code):
    """Vista para mostrar el resultado de la verificación de código"""
    try:
        from checkout_counters.models import ReceiptVerification
        verification = ReceiptVerification.objects.select_related(
            'receipt__payment_link__subscription__client'
        ).get(verification_code=verification_code)
        
        receipt = verification.receipt
        
        # Obtener información del cliente, suscripción y pago
        client = receipt.payment_link.subscription.client
        subscription = receipt.payment_link.subscription
        payment_link = receipt.payment_link
        
        # Verificar si hay un ID de Mercado Pago
        mercadopago_id = receipt.mercadopago_id or "No disponible"
        
        return render(request, 'checkout_counters/verify_code_result.html', {
            'receipt': receipt,
            'client': client,
            'subscription': subscription,
            'payment_link': payment_link,
            'mercadopago_id': mercadopago_id,
            'verification_code': verification_code,
            'is_valid': True
        })
    except ReceiptVerification.DoesNotExist:
        return render(request, 'checkout_counters/verify_code_result.html', {
            'is_valid': False,
            'verification_code': verification_code
        })

def payment_return(request):
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    external_reference = request.GET.get('external_reference')
    
    logger.info(f"Payment return recibido: payment_id={payment_id}, status={status}, external_reference={external_reference}")
    
    try:
        if payment_id and external_reference:
            # Configurar SDK de Mercado Pago
            sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            logger.info(f"Consultando información del pago {payment_id}")
            
            # Obtener información del pago
            payment_info = sdk.payment().get(payment_id)
            logger.info(f"Respuesta de Mercado Pago: {payment_info}")
            
            if payment_info["status"] == 200:
                payment_data = payment_info["response"]
                
                # Usar el manager para actualizar el estado
                payment_link = PaymentLink.objects.update_payment_status(
                    reference_id=external_reference,
                    status=payment_data["status"],
                    payment_data=payment_data
                )
                
                if not payment_link:
                    logger.error(f"No se pudo actualizar el estado del pago: {external_reference}")
                    return redirect('checkout_counters:payment_result', reference_id=external_reference)
                
                if payment_link.is_paid:
                    from .utils import process_successful_payment
                    if process_successful_payment(payment_link, request):
                        logger.info(f"Pago procesado exitosamente: {external_reference}")
                    else:
                        logger.error(f"Error al procesar el comprobante: {external_reference}")
                
                # Siempre redirigir a la vista de resultado
                return redirect('checkout_counters:payment_result', reference_id=external_reference)
    
    except Exception as e:
        logger.error(f"Error processing payment return: {str(e)}")
    
    # En caso de error, también redirigir a la vista de resultado
    if external_reference:
        return redirect('checkout_counters:payment_result', reference_id=external_reference)
    
    # Si no hay referencia, redirigir a una página genérica de error
    return render(request, 'checkout_counters/payment_error.html', {
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL
    })

def download_receipt(request, receipt_number):
    """Vista para descargar un comprobante"""
    receipt = get_object_or_404(Receipt, receipt_number=receipt_number)
    
    # Devolver el archivo PDF si existe
    if receipt.pdf_file:
        response = HttpResponse(receipt.pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante_{receipt.receipt_number}.pdf"'
        return response
    
    # Si no hay archivo PDF, redirigir a una página de error
    messages.error(request, "El comprobante no está disponible")
    return redirect('checkout_counters:payment_list')
