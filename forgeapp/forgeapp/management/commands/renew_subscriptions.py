from django.core.management.base import BaseCommand
from forgeapp.models import Subscription


class Command(BaseCommand):
    help = 'Verifica y renueva todas las suscripciones con auto_renewal activo'

    def handle(self, *args, **options):
        subscriptions = Subscription.objects.filter(status='active', auto_renewal=True)

        renewed_count = 0
        for subscription in subscriptions:
            if subscription.check_and_renew():
                renewed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Renovada: {subscription.client.name} - {subscription.application.name} '
                        f'(Nueva fecha fin: {subscription.end_date})'
                    )
                )

        if renewed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n{renewed_count} suscripción(es) renovada(s) exitosamente.')
            )
        else:
            self.stdout.write(
                self.style.WARNING('No hay suscripciones para renovar.')
            )
