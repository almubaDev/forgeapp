from django.core.management.base import BaseCommand
from django.utils import timezone
from forgeapp.models import Subscription

class Command(BaseCommand):
    help = 'Envía links de pago para suscripciones activas que necesitan pago'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Obtener suscripciones activas que necesitan pago hoy
        subscriptions = Subscription.objects.filter(
            status='active',
            next_payment_date=today
        )

        for subscription in subscriptions:
            try:
                # Generar link de pago
                payment_link = subscription.generate_payment_link()
                
                # Enviar email con el link
                subscription.send_payment_email(payment_link)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Link de pago enviado para suscripción {subscription.reference_id}'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error al procesar suscripción {subscription.reference_id}: {str(e)}'
                    )
                )
