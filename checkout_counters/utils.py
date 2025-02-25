import uuid
import logging
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.utils import timezone
import qrcode
from io import BytesIO
import os

from finance.models import Transaction
from .models import Receipt
from .pdf_generator import generate_payment_receipt

logger = logging.getLogger(__name__)

def process_successful_payment(payment_link, request=None):
    """
    Procesa un pago exitoso:
    1. Crea la transacción
    2. Genera el comprobante
    3. Envía el email
    
    Args:
        payment_link: Instancia de PaymentLink
        request: HttpRequest (opcional, para build_absolute_uri)
    
    Returns:
        bool: True si el proceso fue exitoso, False si hubo error
    """
    try:
        # Verificar si ya existe una transacción para este pago
        transaction_exists = Transaction.objects.filter(
            category='payment_link',
            notes__contains=payment_link.reference_id
        ).exists()

        if not transaction_exists:
            # Crear transacción
            Transaction.objects.create(
                type='income',
                category='payment_link',
                description=payment_link.description,
                amount=payment_link.amount,
                date=timezone.now().date(),
                notes=f"Pago recibido a través de link de pago {payment_link.reference_id}"
            )
            logger.info(f"Transaction created for payment {payment_link.reference_id}")

        # Verificar si ya existe un comprobante
        if hasattr(payment_link, 'receipt'):
            logger.info(f"Receipt already exists for payment {payment_link.reference_id}")
            return True

        # Crear comprobante
        receipt = Receipt.objects.create(
            payment_link=payment_link
        )
        
        # Guardar el ID de Mercado Pago si está disponible
        try:
            if hasattr(payment_link, 'mercadopago_id') and payment_link.mercadopago_id:
                receipt.mercadopago_id = payment_link.mercadopago_id
                receipt.save()
        except Exception as e:
            logger.warning(f"No se pudo guardar mercadopago_id: {str(e)}")
        
        # Crear código de verificación
        from checkout_counters.models import ReceiptVerification
        verification = ReceiptVerification.objects.create(
            receipt=receipt
        )
        
        # Obtener el código de verificación generado automáticamente
        verification_code = verification.verification_code

        # Preparar datos para el PDF
        payment_data = {
            'amount': payment_link.amount,
            'reference_id': payment_link.reference_id,
            'created_at': payment_link.created_at,
            'get_status_display': payment_link.get_status_display
        }
        
        client_data = {
            'company': payment_link.subscription.client.company,
            'rut': payment_link.subscription.client.rut
        }
        
        subscription_id = payment_link.subscription.reference_id
        
        # Generar PDF con el código de verificación
        pdf_buffer = generate_payment_receipt(payment_data, client_data, subscription_id, verification_code)
        
        # Guardar PDF en el modelo
        receipt.pdf_file.save(
            f'comprobante_{receipt.receipt_number}.pdf',
            ContentFile(pdf_buffer.getvalue())
        )

        # Enviar email con el link de descarga
        client_email = payment_link.subscription.client.email if payment_link.subscription else payment_link.payer_email
        if client_email:
            try:
                logger.info(f"Iniciando envío de email a {client_email}")
                
                # Preparar contexto para el email
                download_url = request.build_absolute_uri(
                    reverse('checkout_counters:download_receipt', kwargs={'receipt_number': receipt.receipt_number})
                ) if request else f"{settings.SITE_URL}{reverse('checkout_counters:download_receipt', kwargs={'receipt_number': receipt.receipt_number})}"
                
                context = {
                    'payment': payment_data,
                    'subscription_id': subscription_id,
                    'download_url': download_url,
                    'site_url': settings.SITE_URL
                }
                
                # Renderizar el template de texto plano (como fallback)
                email_text = render_to_string('checkout_counters/email/payment_notification.txt', context)
                
                # Renderizar el template HTML
                email_html = render_to_string('checkout_counters/email/payment_receipt.html', context)
                logger.info("Templates renderizados correctamente")
                
                # Crear el email
                email = EmailMessage(
                    'Comprobante de Pago - ForgeApp',
                    email_text,  # Texto plano como fallback
                    settings.DEFAULT_FROM_EMAIL,
                    [client_email],
                )
                
                # Agregar contenido HTML
                email.content_subtype = "html"  # Establecer el tipo de contenido principal como HTML
                email.body = email_html  # Reemplazar el cuerpo con la versión HTML
                
                # Adjuntar el PDF
                email.attach(
                    f'comprobante_{receipt.receipt_number}.pdf',
                    receipt.pdf_file.read(),
                    'application/pdf'
                )
                
                # Enviar el email
                email.send(fail_silently=False)
                logger.info(f"Email enviado exitosamente a {client_email} con el PDF adjunto")
                
            except Exception as email_error:
                logger.error(f"Error al enviar email: {str(email_error)}")
                # No retornar False aquí, ya que el pago y el comprobante se crearon correctamente

        logger.info(f"Payment {payment_link.reference_id} processed successfully")
        return True

    except Exception as e:
        logger.error(f"Error processing successful payment: {str(e)}")
        return False
