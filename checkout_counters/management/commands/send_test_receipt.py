from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from forgeapp.models import Subscription
from checkout_counters.models import PaymentLink
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Busca una suscripción pagada y envía un comprobante de prueba'

    def add_arguments(self, parser):
        parser.add_argument('--reference_id', type=str, help='ID de referencia de la suscripción (opcional)')
        parser.add_argument('--email', type=str, help='Email al que enviar el comprobante (opcional)')

    def handle(self, *args, **options):
        reference_id = options.get('reference_id')
        test_email = options.get('email')
        
        try:
            # Buscar la suscripción
            if reference_id:
                self.stdout.write(f"Buscando suscripción con ID: {reference_id}")
                subscription = Subscription.objects.get(reference_id=reference_id)
            else:
                self.stdout.write("Buscando la suscripción pagada más reciente...")
                # Buscar la suscripción pagada más reciente
                subscription = Subscription.objects.filter(
                    status='active',
                    last_payment_date__isnull=False
                ).order_by('-last_payment_date').first()
                
                if not subscription:
                    self.stdout.write(
                        self.style.ERROR(
                            "No se encontró ninguna suscripción pagada. "
                            "Intenta especificar un ID de referencia con --reference_id."
                        )
                    )
                    return
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Suscripción encontrada: {subscription.reference_id} - "
                    f"{subscription.client.name} - {subscription.application.name}"
                )
            )
            
            # Buscar el link de pago más reciente para esta suscripción
            payment_link = PaymentLink.objects.filter(
                subscription=subscription,
                status='paid'
            ).order_by('-created_at').first()
            
            if not payment_link:
                self.stdout.write(
                    self.style.ERROR(
                        f"No se encontró ningún link de pago pagado para la suscripción {subscription.reference_id}. "
                        f"Creando un link de pago de prueba..."
                    )
                )
                
                # Crear un link de pago de prueba
                from datetime import timedelta
                import uuid
                
                reference_id = f"{subscription.reference_id}-{timezone.now().strftime('%Y%m%d')}"
                expires_at = timezone.now() + timedelta(days=7)
                
                payment_link = PaymentLink.objects.create(
                    reference_id=reference_id,
                    subscription=subscription,
                    amount=subscription.price,
                    description=f"Pago de prueba para suscripción {subscription.reference_id}",
                    expires_at=expires_at,
                    payment_link=f"https://example.com/pay/{uuid.uuid4()}",
                    status='paid',
                    is_paid=True,
                    payer_email=subscription.client.email
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Link de pago de prueba creado: {payment_link.reference_id}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Link de pago encontrado: {payment_link.reference_id} - "
                        f"Monto: ${payment_link.amount} - Estado: {payment_link.get_status_display()}"
                    )
                )
            
            # Generar y enviar el comprobante
            self.stdout.write("Generando y enviando comprobante...")
            
            # Preparar argumentos para el comando test_receipt_generation
            cmd_args = [payment_link.reference_id]
            cmd_kwargs = {}
            
            if test_email:
                cmd_kwargs['email'] = test_email
                self.stdout.write(f"Usando email de prueba: {test_email}")
            else:
                self.stdout.write(f"Usando email del cliente: {subscription.client.email}")
            
            # Ejecutar el comando test_receipt_generation
            call_command('test_receipt_generation', *cmd_args, **cmd_kwargs)
            
        except Subscription.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"No se encontró ninguna suscripción con el ID de referencia {reference_id}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Error al enviar el comprobante de prueba: {str(e)}"
                )
            )
