from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

def check_expired_subscriptions():
    """Verifica y actualiza suscripciones vencidas"""
    try:
        from forgeapp.models import Subscription
        
        with transaction.atomic():
            # Obtener suscripciones activas que han expirado
            expired_subscriptions = Subscription.objects.select_for_update().filter(
                status='active',
                end_date__lt=timezone.now().date()
            )

            # Marcar como expiradas
            count = 0
            for subscription in expired_subscriptions:
                subscription.status = 'expired'
                subscription.save()
                count += 1

            if count > 0:
                logger.info(f"Se marcaron {count} suscripciones como expiradas")

    except Exception as e:
        logger.error(f"Error al verificar suscripciones: {e}")

def generate_monthly_payments():
    """Genera pagos pendientes para todas las suscripciones activas"""
    try:
        # Verificar si ya se generaron los pagos este mes
        today = timezone.now().date()
        cache_key = f'monthly_payments_generated_{today.year}_{today.month}'
        
        if not cache.get(cache_key):
            call_command('generate_pending_payments')
            cache.set(cache_key, True, timeout=60*60*24*28)  # Expira en 28 días
            logger.info("Pagos mensuales generados exitosamente")
    except Exception as e:
        logger.error(f"Error al generar pagos mensuales: {e}")

def daily_tasks():
    """Ejecuta las tareas diarias"""
    try:
        # Verificar suscripciones vencidas
        check_expired_subscriptions()
        
        # Si es el primer día del mes, generar pagos
        if timezone.now().date().day == 1:
            generate_monthly_payments()
            
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
