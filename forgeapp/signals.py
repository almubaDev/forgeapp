# forgeapp/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Subscription, PaymentEvent

logger = logging.getLogger('forgeapp')

@receiver(post_save, sender=Subscription)
def generate_payment_event_on_activation(sender, instance, created, **kwargs):
    """
    Genera automáticamente un evento de pago cuando:
    1. Se crea una nueva suscripción ACTIVE
    2. Una suscripción pasa a estado ACTIVE desde otro estado

    Solo genera un evento si no existe ninguno pendiente.

    IMPORTANTE: El primer pago es ADELANTADO, por lo que la fecha estimada
    es la fecha de inicio (start_date), no current_period_end.
    """
    # Solo generar evento si la suscripción está activa
    if instance.status != 'active':
        return

    # Verificar si ya existe un evento pendiente
    has_pending = instance.payment_events.filter(status='pending').exists()
    if has_pending:
        logger.debug(f"Suscripción {instance.reference_id} ya tiene evento pendiente, no se genera nuevo")
        return

    # Generar nuevo evento de pago
    # El primer pago es adelantado, por lo que la fecha esperada es start_date
    event = PaymentEvent.objects.create(
        subscription=instance,
        expected_date=instance.start_date,  # Primer pago adelantado
        amount=instance.price,
        status='pending',
        notes='Evento generado automáticamente al activar suscripción (pago adelantado)'
    )

    logger.info(f"Evento de pago generado para suscripción {instance.reference_id}: {event.id} con fecha {event.expected_date}")


@receiver(post_save, sender=PaymentEvent)
def generate_next_payment_event_on_paid(sender, instance, created, **kwargs):
    """
    Genera automáticamente el siguiente evento de pago cuando:
    1. Un evento es marcado como PAID
    2. La suscripción tiene auto_renewal=True
    3. No existe otro evento pendiente
    """
    # Solo procesar si el evento fue marcado como pagado (no es nueva creación)
    if created:
        return

    # Solo procesar eventos pagados
    if instance.status != 'paid':
        return

    subscription = instance.subscription

    # Solo generar siguiente evento si tiene auto-renovación
    if not subscription.auto_renewal:
        logger.debug(f"Suscripción {subscription.reference_id} no tiene auto-renovación, no se genera siguiente evento")
        return

    # Verificar que no exista ya un evento pendiente
    has_pending = subscription.payment_events.filter(status='pending').exists()
    if has_pending:
        logger.debug(f"Suscripción {subscription.reference_id} ya tiene evento pendiente, no se genera siguiente")
        return

    # Generar siguiente evento de pago
    # La fecha esperada es el current_period_end de la suscripción (que ya fue actualizado)
    next_event = PaymentEvent.objects.create(
        subscription=subscription,
        expected_date=subscription.current_period_end,
        amount=subscription.price,
        status='pending',
        notes='Evento generado automáticamente tras pago anterior'
    )

    logger.info(f"Siguiente evento de pago generado para suscripción {subscription.reference_id}: {next_event.id} con fecha {next_event.expected_date}")
