from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from threading import Timer
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Inicia la verificación periódica de suscripciones vencidas'

    def handle(self, *args, **options):
        def check_expired_subscriptions():
            """Verifica y actualiza suscripciones vencidas"""
            try:
                from forgeapp.models import Subscription
                
                expired_subscriptions = Subscription.objects.filter(
                    status='active',
                    end_date__lt=timezone.now().date()
                )

                for subscription in expired_subscriptions:
                    subscription.status = 'expired'
                    subscription.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Suscripción {subscription.id} marcada como expirada'
                        )
                    )
            except Exception as e:
                logger.error(f"Error al verificar suscripciones: {e}")
                self.stderr.write(self.style.ERROR(f'Error: {e}'))

        def schedule_subscription_check():
            try:
                last_check = cache.get('last_subscription_check')
                now = timezone.now()
                
                if not last_check or last_check.date() < now.date():
                    check_expired_subscriptions()
                    cache.set('last_subscription_check', now)

                next_check = timezone.now() + timedelta(days=1)
                next_check = next_check.replace(hour=0, minute=0, second=0, microsecond=0)
                delay = (next_check - timezone.now()).total_seconds()
                
                Timer(delay, schedule_subscription_check).start()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Próxima verificación programada para {next_check}'
                    )
                )
            except Exception as e:
                logger.error(f"Error al programar verificación: {e}")
                self.stderr.write(self.style.ERROR(f'Error: {e}'))

        self.stdout.write('Iniciando verificación de suscripciones...')
        schedule_subscription_check()
