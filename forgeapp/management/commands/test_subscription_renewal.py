from django.core.management.base import BaseCommand
from django.utils import timezone
from forgeapp.models import Subscription
import logging

logger = logging.getLogger('forgeapp')

class Command(BaseCommand):
    help = 'Prueba la renovación automática de una suscripción específica'

    def add_arguments(self, parser):
        parser.add_argument('reference_id', type=str, help='ID de referencia de la suscripción a renovar')

    def handle(self, *args, **options):
        reference_id = options['reference_id']
        
        try:
            # Obtener la suscripción
            subscription = Subscription.objects.get(reference_id=reference_id)
            
            # Verificar si la suscripción tiene la renovación automática activada
            if not subscription.auto_renewal:
                self.stdout.write(
                    self.style.WARNING(
                        f'La suscripción {reference_id} no tiene la renovación automática activada. '
                        f'Activando temporalmente para la prueba.'
                    )
                )
                subscription.auto_renewal = True
            
            # Verificar si la suscripción está activa
            if subscription.status != 'active':
                self.stdout.write(
                    self.style.WARNING(
                        f'La suscripción {reference_id} no está activa. '
                        f'Activando temporalmente para la prueba.'
                    )
                )
                subscription.status = 'active'
            
            # Establecer la fecha de fin a hoy para simular que ha llegado a su fecha de fin
            today = timezone.now().date()
            self.stdout.write(
                self.style.WARNING(
                    f'Estableciendo la fecha de fin de la suscripción {reference_id} a hoy ({today}) '
                    f'para simular que ha llegado a su fecha de fin.'
                )
            )
            subscription.end_date = today
            
            # Guardar cambios
            subscription.save()
            
            # Ejecutar el comando de renovación
            from django.core.management import call_command
            self.stdout.write(self.style.SUCCESS(f'Ejecutando el comando de renovación...'))
            call_command('renew_subscriptions')
            
            # Verificar si la suscripción se renovó correctamente
            subscription.refresh_from_db()
            if subscription.end_date > today:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'La suscripción {reference_id} se renovó correctamente. '
                        f'Nueva fecha de fin: {subscription.end_date}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'La suscripción {reference_id} no se renovó correctamente. '
                        f'Fecha de fin: {subscription.end_date}'
                    )
                )
            
            # Verificar si se generó un link de pago (solo para suscripciones anuales)
            if subscription.payment_type == 'annual':
                # Verificar si se generó un link de pago hoy
                payment_link = subscription.payment_links.filter(
                    created_at__date=today
                ).first()
                
                if payment_link:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Se generó un link de pago para la suscripción {reference_id}: '
                            f'{payment_link.payment_link}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'No se generó un link de pago para la suscripción {reference_id}. '
                            f'Esto es normal si la suscripción es mensual, pero no si es anual.'
                        )
                    )
            
        except Subscription.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'No se encontró ninguna suscripción con el ID de referencia {reference_id}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error al probar la renovación de la suscripción {reference_id}: {str(e)}'
                )
            )
