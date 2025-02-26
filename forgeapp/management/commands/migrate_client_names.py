from django.core.management.base import BaseCommand
from forgeapp.models import Client

class Command(BaseCommand):
    help = 'Migra los nombres de clientes existentes a los nuevos campos first_name y last_name'

    def handle(self, *args, **options):
        clients = Client.objects.all()
        updated_count = 0

        for client in clients:
            # Si first_name o last_name ya tienen valores, no los modificamos
            if client.first_name or client.last_name:
                continue

            # Dividir el nombre en first_name y last_name
            name_parts = client.name.split()
            if name_parts:
                client.first_name = name_parts[0]
                if len(name_parts) > 1:
                    client.last_name = ' '.join(name_parts[1:])
                # Guardar sin actualizar el campo name (ya que se actualizará automáticamente)
                client.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Se actualizaron {updated_count} clientes'))
