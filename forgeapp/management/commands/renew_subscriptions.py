from django.core.management.base import BaseCommand
from django.utils import timezone
from forgeapp.models import Subscription
from datetime import timedelta
import logging

logger = logging.getLogger('forgeapp')

class Command(BaseCommand):
    help = 'Renueva automáticamente las suscripciones que han llegado a su fecha de fin y tienen la renovación automática activada'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Obtener suscripciones activas que han llegado a su fecha de fin y tienen la renovación automática activada
        subscriptions_to_renew = Subscription.objects.filter(
            status='active',
            end_date__lte=today,
            auto_renewal=True
        )
        
        self.stdout.write(f"Encontradas {subscriptions_to_renew.count()} suscripciones para renovar")
        
        for subscription in subscriptions_to_renew:
            try:
                # Calcular nueva fecha de fin (1 año después de la fecha de fin actual)
                new_end_date = subscription.end_date + timedelta(days=365)
                
                # Actualizar fecha de fin
                subscription.end_date = new_end_date
                
                # Actualizar fecha de próximo pago si es necesario
                if subscription.next_payment_date is None or subscription.next_payment_date < today:
                    # Si es mensual, el próximo pago es en un mes
                    if subscription.payment_type == 'monthly':
                        from dateutil.relativedelta import relativedelta
                        subscription.next_payment_date = today + relativedelta(months=1)
                    # Si es anual, el próximo pago es hoy
                    else:
                        subscription.next_payment_date = today
                
                # Guardar cambios
                subscription.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Suscripción {subscription.reference_id} renovada hasta {new_end_date}'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error al renovar suscripción {subscription.reference_id}: {str(e)}'
                    )
                )
