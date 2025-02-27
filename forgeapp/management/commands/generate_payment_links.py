from django.core.management.base import BaseCommand
from django.utils import timezone
from forgeapp.models import Subscription
import logging

logger = logging.getLogger('forgeapp')

class Command(BaseCommand):
    help = 'Genera links de pago para suscripciones activas que lo necesiten'

    def handle(self, *args, **options):
        logger.info("Iniciando generación automática de links de pago")
        
        # Obtener todas las suscripciones activas
        active_subscriptions = Subscription.objects.filter(status='active')
        
        for subscription in active_subscriptions:
            try:
                if subscription.can_register_payment():
                    logger.info(f"Generando link de pago para suscripción {subscription.reference_id}")
                    logger.info(f"Último pago: {subscription.last_payment_date}")
                    logger.info(f"Próximo pago: {subscription.next_payment_date}")
                    
                    # Generar link de pago sin request (es un comando de consola)
                    # El método generate_payment_link manejará las URLs usando settings.SITE_URL
                    payment_link = subscription.generate_payment_link(request=None)
                    
                    if payment_link:
                        # Enviar email con el link de pago
                        subscription.send_payment_email(payment_link)
                        logger.info(f"Link de pago generado y enviado exitosamente para suscripción {subscription.reference_id}")
                    else:
                        logger.error(f"No se pudo generar el link de pago para suscripción {subscription.reference_id}")
                else:
                    logger.info(f"La suscripción {subscription.reference_id} no necesita un nuevo link de pago")
                    if subscription.last_payment_date:
                        logger.info(f"Último pago: {subscription.last_payment_date}")
                    if subscription.next_payment_date:
                        logger.info(f"Próximo pago: {subscription.next_payment_date}")
                    if subscription.has_pending_payment():
                        logger.info("Tiene un pago pendiente")
            except Exception as e:
                logger.error(f"Error al procesar suscripción {subscription.reference_id}: {str(e)}")
        
        logger.info("Finalizada la generación automática de links de pago")
