from django.core.management.base import BaseCommand
from django.utils import timezone
from forgeapp.models import Subscription
import logging

logger = logging.getLogger('forgeapp')

class Command(BaseCommand):
    help = 'Verifica suscripciones que necesitan pago y actualiza su estado visual'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Buscar suscripciones activas cuya fecha de próximo pago haya llegado o pasado
        subscriptions_needing_payment = Subscription.objects.filter(
            status='active',
            next_payment_date__lte=today
        )
        
        count = subscriptions_needing_payment.count()
        self.stdout.write(f"Se encontraron {count} suscripciones que necesitan pago")
        logger.info(f"Se encontraron {count} suscripciones que necesitan pago")
        
        # Registrar cada suscripción que necesita pago
        for subscription in subscriptions_needing_payment:
            self.stdout.write(f"  - {subscription.reference_id}: {subscription.client.name} - {subscription.application.name}")
            logger.info(f"Suscripción {subscription.reference_id} necesita pago (Cliente: {subscription.client.name})")
            
            # Opcionalmente, aquí se podría enviar una notificación por correo electrónico
            # al administrador o al cliente sobre el pago pendiente
