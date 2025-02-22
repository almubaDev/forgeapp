from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'

    def ready(self):
        # Solo inicializar si no estamos en modo migración y no es un worker
        if (not settings.MIGRATION_MODULES and 
            not getattr(settings, 'RUN_MAIN', False) and 
            not getattr(settings, 'IS_WORKER', False)):
            
            try:
                # Registrar signals
                from finance.signals import register_signals
                register_signals()

                # Iniciar scheduler solo si está habilitado
                if getattr(settings, 'ENABLE_SUBSCRIPTION_CHECK', True):
                    from finance.scheduler import start_scheduler
                    start_scheduler()
                    
            except Exception as e:
                logger.error(f"Error durante la inicialización de finance: {e}")
