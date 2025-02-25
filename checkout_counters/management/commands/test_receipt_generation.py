from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from checkout_counters.models import PaymentLink, Receipt
from checkout_counters.utils import process_successful_payment
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Prueba la generación y envío de comprobantes de pago'

    def add_arguments(self, parser):
        parser.add_argument('reference_id', type=str, help='ID de referencia del link de pago')
        parser.add_argument('--email', type=str, help='Email al que enviar el comprobante (opcional)')

    def handle(self, *args, **options):
        reference_id = options['reference_id']
        test_email = options.get('email')
        
        try:
            # Obtener el link de pago
            payment_link = PaymentLink.objects.get(reference_id=reference_id)
            
            # Verificar si el link de pago ya tiene un comprobante
            has_receipt = hasattr(payment_link, 'receipt')
            
            if has_receipt:
                self.stdout.write(
                    self.style.WARNING(
                        f'El link de pago {reference_id} ya tiene un comprobante. '
                        f'Se eliminará para generar uno nuevo.'
                    )
                )
                payment_link.receipt.delete()
            
            # Verificar si el link de pago está pagado
            if not payment_link.is_paid:
                self.stdout.write(
                    self.style.WARNING(
                        f'El link de pago {reference_id} no está marcado como pagado. '
                        f'Marcándolo temporalmente como pagado para la prueba.'
                    )
                )
                payment_link.is_paid = True
                payment_link.status = 'paid'
                payment_link.save()
            
            # Si se proporcionó un email de prueba, guardar el email original y usar el de prueba
            original_email = None
            if test_email and payment_link.subscription:
                original_email = payment_link.subscription.client.email
                self.stdout.write(
                    self.style.WARNING(
                        f'Usando email de prueba {test_email} en lugar de {original_email}'
                    )
                )
                payment_link.subscription.client.email = test_email
                payment_link.subscription.client.save()
            elif test_email:
                original_email = payment_link.payer_email
                self.stdout.write(
                    self.style.WARNING(
                        f'Usando email de prueba {test_email} en lugar de {original_email}'
                    )
                )
                payment_link.payer_email = test_email
                payment_link.save()
            
            # Procesar el pago exitoso (generar comprobante y enviar email)
            self.stdout.write(self.style.SUCCESS(f'Procesando pago {reference_id}...'))
            result = process_successful_payment(payment_link)
            
            # Verificar el resultado
            if result:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Comprobante generado y enviado exitosamente para el pago {reference_id}'
                    )
                )
                
                # Mostrar información del comprobante
                receipt = Receipt.objects.get(payment_link=payment_link)
                self.stdout.write(f'Número de comprobante: {receipt.receipt_number}')
                self.stdout.write(f'Código secreto: {receipt.secret_code}')
                self.stdout.write(f'URL de verificación: {settings.SITE_URL}/checkout/receipt/verify/{receipt.secret_code}/')
                self.stdout.write(f'URL de descarga: {settings.SITE_URL}/checkout/receipt/download/{receipt.receipt_number}/')
                
                if test_email:
                    self.stdout.write(f'Email enviado a: {test_email}')
                else:
                    client_email = payment_link.subscription.client.email if payment_link.subscription else payment_link.payer_email
                    self.stdout.write(f'Email enviado a: {client_email}')
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error al generar el comprobante para el pago {reference_id}'
                    )
                )
            
            # Restaurar el email original si se usó uno de prueba
            if original_email:
                if payment_link.subscription:
                    payment_link.subscription.client.email = original_email
                    payment_link.subscription.client.save()
                else:
                    payment_link.payer_email = original_email
                    payment_link.save()
                
                self.stdout.write(f'Email restaurado a: {original_email}')
            
        except PaymentLink.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'No se encontró ningún link de pago con el ID de referencia {reference_id}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error al probar la generación del comprobante: {str(e)}'
                )
            )
