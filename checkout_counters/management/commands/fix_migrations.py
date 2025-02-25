from django.core.management.base import BaseCommand
import os
import glob
import re
from django.db import connection

class Command(BaseCommand):
    help = 'Corrige las migraciones problemáticas'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando corrección de migraciones...")
        
        # 1. Eliminar migraciones problemáticas
        self.delete_problematic_migrations()
        
        # 2. Actualizar la tabla django_migrations
        self.update_migrations_table()
        
        # 3. Crear una migración vacía
        self.create_empty_migration()
        
        self.stdout.write(self.style.SUCCESS("Migraciones corregidas exitosamente"))
    
    def delete_problematic_migrations(self):
        """Elimina las migraciones problemáticas"""
        migration_dir = 'checkout_counters/migrations'
        
        # Buscar migraciones que contengan 'receiptverification'
        pattern = os.path.join(migration_dir, '*receiptverification*.py')
        problematic_files = glob.glob(pattern)
        
        if not problematic_files:
            self.stdout.write("No se encontraron migraciones problemáticas")
            return
        
        for file_path in problematic_files:
            try:
                os.remove(file_path)
                self.stdout.write(self.style.SUCCESS(f"Eliminada migración: {os.path.basename(file_path)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al eliminar {file_path}: {str(e)}"))
    
    def update_migrations_table(self):
        """Actualiza la tabla django_migrations para eliminar referencias a migraciones problemáticas"""
        with connection.cursor() as cursor:
            # Buscar migraciones de checkout_counters que contengan 'receiptverification'
            cursor.execute(
                "SELECT id, name FROM django_migrations WHERE app = 'checkout_counters' AND name LIKE '%receiptverification%'"
            )
            problematic_migrations = cursor.fetchall()
            
            if not problematic_migrations:
                self.stdout.write("No se encontraron registros de migraciones problemáticas en la base de datos")
                return
            
            for migration_id, migration_name in problematic_migrations:
                try:
                    cursor.execute(
                        "DELETE FROM django_migrations WHERE id = ?",
                        (migration_id,)
                    )
                    self.stdout.write(self.style.SUCCESS(f"Eliminado registro de migración: {migration_name}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error al eliminar registro de migración {migration_name}: {str(e)}"))
    
    def create_empty_migration(self):
        """Crea una migración vacía para checkout_counters"""
        import subprocess
        
        try:
            result = subprocess.run(
                ['python', 'manage.py', 'makemigrations', '--empty', 'checkout_counters'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS("Migración vacía creada exitosamente"))
                self.stdout.write(result.stdout)
            else:
                self.stdout.write(self.style.ERROR(f"Error al crear migración vacía: {result.stderr}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al ejecutar comando: {str(e)}"))
