from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

def check_expired_subscriptions():
    """
    Verifica y actualiza suscripciones vencidas.
    Una suscripción se marca como EXPIRED solo si pasaron más de 15 días desde su fecha de renovación esperada.
    Requiere que la suscripción tenga start_date (no sea PENDING).
    """
    try:
        from forgeapp.models import Subscription
        from datetime import date

        with transaction.atomic():
            # Obtener todas las suscripciones activas con fecha de inicio
            active_subscriptions = Subscription.objects.select_for_update().filter(
                status='active',
                start_date__isnull=False  # Solo suscripciones con fecha de inicio
            )

            # Verificar cuáles han expirado (pasó el período de gracia de 15 días)
            count = 0
            today = date.today()

            for subscription in active_subscriptions:
                # Verificar si pasó el período de gracia
                if subscription.grace_period_end and today > subscription.grace_period_end:
                    subscription.status = 'expired'
                    subscription.save()
                    count += 1
                    logger.info(f"Suscripción {subscription.reference_id} marcada como expirada (venció el {subscription.grace_period_end})")

            if count > 0:
                logger.info(f"Se marcaron {count} suscripciones como expiradas")

    except Exception as e:
        logger.error(f"Error al verificar suscripciones: {e}")

def daily_tasks():
    """
    Ejecuta las tareas diarias.
    NOTA: La generación de eventos de pago se hace automáticamente mediante signals
    cuando se activa una suscripción o se marca un evento como pagado.
    """
    try:
        # Verificar suscripciones vencidas
        check_expired_subscriptions()

    except Exception as e:
        logger.error(f"Error en tareas diarias: {e}")

def start_scheduler():
    """Inicia el scheduler de forma segura"""
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # Programar tareas diarias a las 00:00
        scheduler.add_job(
            daily_tasks,
            trigger='cron',
            hour=0,
            minute=0,
            id='daily_tasks',
            replace_existing=True,
            jobstore='default'
        )

        scheduler.start()
        logger.info("Scheduler iniciado exitosamente")
        
        # Ejecutar tareas inmediatamente al iniciar
        daily_tasks()
        
    except Exception as e:
        logger.error(f"Error al iniciar el scheduler: {e}")
