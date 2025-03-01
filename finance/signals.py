from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.apps import apps
from django.db.models import Q
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def register_signals():
    """Registra los signals una vez que la aplicación está lista"""
    Subscription = apps.get_model('forgeapp', 'Subscription')
    Payment = apps.get_model('finance', 'Payment')
    Transaction = apps.get_model('finance', 'Transaction')

    @receiver(post_save, sender=Payment)
    def handle_payment_changes(sender, instance, created, **kwargs):
        """Maneja cambios en pagos"""
        try:
            if instance.subscription:
                subscription = instance.subscription

                # Si el pago está completado
                if instance.status == 'completed':
                    subscription.status = 'active'
                    
                    # Extender la fecha de fin según el tipo de pago
                    if subscription.payment_type == 'monthly':
                        current_end = max(subscription.end_date, timezone.now().date())
                        subscription.end_date = current_end + timedelta(days=30)
                    elif subscription.payment_type == 'annual':
                        current_end = max(subscription.end_date, timezone.now().date())
                        subscription.end_date = current_end + timedelta(days=365)

                    subscription.save()

                    # Crear transacción de ingreso
                    Transaction.objects.create(
                        type='income',
                        category='Pago de Suscripción',
                        description=f'Pago recibido - {subscription.client.name} - {subscription.application.name}',
                        amount=instance.amount,
                        date=instance.payment_date.date() if instance.payment_date else timezone.now().date(),
                        payment=instance,
                        notes='Ingreso registrado automáticamente por pago completado'
                    )
                    logger.info(f'Transacción de ingreso creada para pago {instance.id}')

                # Si el pago falló o fue cancelado
                elif instance.status in ['failed', 'cancelled']:
                    # Verificar si hay otros pagos pendientes o completados
                    # Usar finance_payments en lugar de payments
                    pending_or_completed = Payment.objects.filter(
                        subscription=subscription,
                        status__in=['pending', 'completed']
                    ).exclude(id=instance.id).exists()
                    
                    if not pending_or_completed:
                        subscription.status = 'cancelled'
                        subscription.save()

        except Exception as e:
            logger.error(f'Error al manejar cambios en pago: {e}')