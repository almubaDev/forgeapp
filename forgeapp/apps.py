from django.apps import AppConfig


class ForgeappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forgeapp'

    def ready(self):
        """Import signals when the app is ready"""
        import forgeapp.signals
