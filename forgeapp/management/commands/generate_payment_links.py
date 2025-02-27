from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from forgeapp.models import Subscription
import logging
import sys

logger = logging.getLogger('forgeapp')

class Command(BaseCommand):
    help = 'Genera links de pago para suscripciones activas que lo necesiten'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué se haría sin realizar cambios'
        )

    def setup_logging(self):
        """Configura el logging para el comando"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def handle(self, *args, **options):
        self.setup_logging()
        dry_run = options['dry_run']
        
        if dry_run:
            logger.info("Ejecutando en modo dry-run (sin realizar cambios)")
        
        logger.info("Iniciando generación automática de links de pago")
        logger.info(f"Usando SITE_URL: {settings.SITE_URL}")
        
        try:
            with transaction.atomic():
                # Obtener todas las suscripciones activas
                active_subscriptions = Subscription.objects.filter(status='active')
                logger.info(f"Encontradas {active_subscriptions.count()} suscripciones activas")
                
                links_generated = 0
                errors = 0
                
                for subscription in active_subscriptions:
                    try:
                        if subscription.can_register_payment():
                            logger.info(f"Procesando suscripción {subscription.reference_id}")
                            logger.info(f"- Cliente: {subscription.client.name}")
                            logger.info(f"- Último pago: {subscription.last_payment_date}")
                            logger.info(f"- Próximo pago: {subscription.next_payment_date}")
                            
                            if not dry_run:
                                # Generar link de pago
                                payment_link = subscription.generate_payment_link(request=None)
                                
                                if payment_link:
                                    # Enviar email con el link de pago
                                    subscription.send_payment_email(payment_link)
                                    logger.info(f"✓ Link de pago generado y enviado: {payment_link.payment_link}")
                                    links_generated += 1
                                else:
                                    logger.error(f"✗ No se pudo generar el link de pago")
                                    errors += 1
                            else:
                                logger.info("✓ [DRY-RUN] Se generaría link de pago")
                                links_generated += 1
                        else:
                            logger.info(f"Saltando suscripción {subscription.reference_id}")
                            logger.info("Razones:")
                            if subscription.has_pending_payment():
                                logger.info("- Tiene un pago pendiente")
                            if subscription.last_payment_date:
                                logger.info(f"- Último pago: {subscription.last_payment_date}")
                            if subscription.next_payment_date:
                                logger.info(f"- Próximo pago: {subscription.next_payment_date}")
                    except Exception as e:
                        logger.error(f"Error al procesar suscripción {subscription.reference_id}: {str(e)}")
                        errors += 1
                
                if dry_run:
                    logger.info("\nResumen (dry-run):")
                    logger.info(f"- Se generarían {links_generated} links de pago")
                    if errors > 0:
                        logger.info(f"- Se encontraron {errors} errores potenciales")
                    transaction.set_rollback(True)
                else:
                    logger.info("\nResumen:")
                    logger.info(f"- Links de pago generados: {links_generated}")
                    if errors > 0:
                        logger.info(f"- Errores encontrados: {errors}")
        
        except Exception as e:
            logger.error(f"Error general: {str(e)}")
            return
        
        logger.info("Finalizada la generación automática de links de pago")
