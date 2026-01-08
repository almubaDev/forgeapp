# forgeapp/management/commands/check_expirations.py
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date
import logging

logger = logging.getLogger('forgeapp')


class Command(BaseCommand):
    help = 'Verifica suscripciones activas y marca como EXPIRED las que pasaron el período de gracia de 15 días'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué suscripciones se marcarían como expiradas sin realizar cambios',
        )

    def handle(self, *args, **options):
        from forgeapp.models import Subscription

        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY RUN - No se realizarán cambios'))

        today = date.today()

        with transaction.atomic():
            # Obtener todas las suscripciones activas
            active_subscriptions = Subscription.objects.select_for_update().filter(
                status='active'
            )

            expired_count = 0

            for subscription in active_subscriptions:
                # Verificar si pasó el período de gracia (15 días después de current_period_end)
                if today > subscription.grace_period_end:
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'[DRY RUN] Suscripción {subscription.reference_id} sería marcada como EXPIRED '
                                f'(venció el {subscription.grace_period_end.strftime("%d/%m/%Y")})'
                            )
                        )
                    else:
                        subscription.status = 'expired'
                        subscription.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Suscripción {subscription.reference_id} marcada como EXPIRED '
                                f'(venció el {subscription.grace_period_end.strftime("%d/%m/%Y")})'
                            )
                        )
                        logger.info(
                            f'Suscripción {subscription.reference_id} marcada como expirada '
                            f'(venció el {subscription.grace_period_end})'
                        )

                    expired_count += 1

            if expired_count == 0:
                self.stdout.write(self.style.SUCCESS('No hay suscripciones expiradas'))
            else:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n[DRY RUN] {expired_count} suscripción(es) serían marcadas como expiradas'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n{expired_count} suscripción(es) marcadas como expiradas exitosamente'
                        )
                    )
                    logger.info(f'Se marcaron {expired_count} suscripciones como expiradas')
