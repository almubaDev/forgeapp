from django.core.management.base import BaseCommand
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Corrige el modelo Receipt y crea el modelo ReceiptVerification'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando corrección de la base de datos...")
        
        # Eliminar las migraciones problemáticas
        self.delete_migration_files()
        
        # Ejecutar SQL para corregir la base de datos
        with connection.cursor() as cursor:
            # 1. Verificar si la tabla ReceiptVerification ya existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkout_counters_receiptverification'")
            receipt_verification_exists = cursor.fetchone() is not None
            
            if receipt_verification_exists:
                self.stdout.write("La tabla ReceiptVerification ya existe, eliminándola...")
                cursor.execute("DROP TABLE checkout_counters_receiptverification")
            
            # 2. Verificar si la columna verification_code existe en Receipt
            cursor.execute("PRAGMA table_info(checkout_counters_receipt)")
            columns = cursor.fetchall()
            has_verification_code = any(col[1] == 'verification_code' for col in columns)
            
            if has_verification_code:
                self.stdout.write("Eliminando la columna verification_code de Receipt...")
                
                # En SQLite, no se puede eliminar una columna directamente, 
                # así que tenemos que recrear la tabla sin esa columna
                
                # 2.1. Obtener la estructura actual de la tabla
                cursor.execute("PRAGMA table_info(checkout_counters_receipt)")
                columns = cursor.fetchall()
                
                # 2.2. Crear una tabla temporal sin la columna verification_code
                create_table_sql = "CREATE TABLE checkout_counters_receipt_temp ("
                column_defs = []
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    col_notnull = "NOT NULL" if col[3] == 1 else ""
                    col_default = f"DEFAULT {col[4]}" if col[4] is not None else ""
                    col_pk = "PRIMARY KEY" if col[5] == 1 else ""
                    
                    if col_name != 'verification_code':
                        column_defs.append(f"{col_name} {col_type} {col_notnull} {col_default} {col_pk}")
                
                create_table_sql += ", ".join(column_defs) + ")"
                cursor.execute(create_table_sql)
                
                # 2.3. Copiar los datos de la tabla original a la temporal
                cursor.execute("PRAGMA table_info(checkout_counters_receipt)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns if col[1] != 'verification_code']
                
                copy_sql = f"""
                INSERT INTO checkout_counters_receipt_temp ({', '.join(column_names)})
                SELECT {', '.join(column_names)}
                FROM checkout_counters_receipt
                """
                cursor.execute(copy_sql)
                
                # 2.4. Eliminar la tabla original
                cursor.execute("DROP TABLE checkout_counters_receipt")
                
                # 2.5. Renombrar la tabla temporal a la original
                cursor.execute("ALTER TABLE checkout_counters_receipt_temp RENAME TO checkout_counters_receipt")
                
                # 2.6. Recrear los índices
                cursor.execute("CREATE INDEX checkout_counters_receipt_payment_link_id ON checkout_counters_receipt(payment_link_id)")
                
                self.stdout.write(self.style.SUCCESS("Columna verification_code eliminada exitosamente"))
            else:
                self.stdout.write("La columna verification_code no existe en la tabla Receipt")
            
            # 3. Crear la tabla ReceiptVerification
            self.stdout.write("Creando la tabla ReceiptVerification...")
            cursor.execute("""
            CREATE TABLE checkout_counters_receiptverification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verification_code VARCHAR(20) UNIQUE NOT NULL,
                created_at DATETIME NOT NULL,
                receipt_id INTEGER NOT NULL REFERENCES checkout_counters_receipt(id) UNIQUE
            )
            """)
            
            # 4. Crear el índice para receipt_id
            cursor.execute("CREATE INDEX checkout_counters_receiptverification_receipt_id ON checkout_counters_receiptverification(receipt_id)")
            
            self.stdout.write(self.style.SUCCESS("Tabla ReceiptVerification creada exitosamente"))
        
        # Crear una nueva migración
        self.stdout.write("Creando una nueva migración...")
        os.system("python manage.py makemigrations --empty checkout_counters")
        
        self.stdout.write(self.style.SUCCESS("Corrección de la base de datos completada"))
    
    def delete_migration_files(self):
        """Elimina las migraciones problemáticas"""
        migration_dir = 'checkout_counters/migrations'
        migrations_to_delete = [
            '0010_receipt_mercadopago_id_receipt_verification_code.py',
            '0011_alter_receipt_verification_code.py',
            '0012_remove_receipt_verification_code_receiptverification.py'
        ]
        
        for migration in migrations_to_delete:
            migration_path = os.path.join(migration_dir, migration)
            if os.path.exists(migration_path):
                try:
                    os.remove(migration_path)
                    self.stdout.write(f"Eliminada migración: {migration}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"No se pudo eliminar la migración {migration}: {str(e)}"))
