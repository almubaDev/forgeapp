from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
import random
import string
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Genera códigos de verificación para los comprobantes existentes'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando generación de códigos de verificación...")
        
        # Verificar si la tabla ReceiptVerification existe
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkout_counters_receiptverification'")
            receipt_verification_exists = cursor.fetchone() is not None
            
            if not receipt_verification_exists:
                self.stdout.write(self.style.ERROR("La tabla ReceiptVerification no existe. Ejecuta primero 'python manage.py fix_receipt_model'"))
                return
            
            # Obtener todos los comprobantes
            cursor.execute("SELECT id, receipt_number FROM checkout_counters_receipt")
            receipts = cursor.fetchall()
            
            total_receipts = len(receipts)
            self.stdout.write(f"Encontrados {total_receipts} comprobantes")
            
            created_count = 0
            
            for receipt_id, receipt_number in receipts:
                try:
                    # Verificar si ya tiene un código de verificación
                    cursor.execute(
                        "SELECT verification_code FROM checkout_counters_receiptverification WHERE receipt_id = ?",
                        (receipt_id,)
                    )
                    existing_verification = cursor.fetchone()
                    
                    if existing_verification:
                        self.stdout.write(
                            self.style.WARNING(
                                f"El comprobante {receipt_number} ya tiene un código de verificación: {existing_verification[0]}"
                            )
                        )
                        continue
                    
                    # Generar un código alfanumérico único
                    code = self.generate_verification_code(cursor)
                    
                    # Crear el código de verificación
                    now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute(
                        """
                        INSERT INTO checkout_counters_receiptverification 
                        (verification_code, created_at, receipt_id) 
                        VALUES (?, ?, ?)
                        """,
                        (code, now, receipt_id)
                    )
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Código de verificación generado para el comprobante {receipt_number}: {code}"
                        )
                    )
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error al generar código de verificación para el comprobante {receipt_number}: {str(e)}"
                        )
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Se generaron {created_count} códigos de verificación de un total de {total_receipts} comprobantes"
                )
            )
    
    def generate_verification_code(self, cursor):
        """Genera un código alfanumérico único para verificación"""
        # Generar un código alfanumérico de 8 caracteres
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(chars) for _ in range(8))
        
        # Verificar que sea único
        cursor.execute(
            "SELECT COUNT(*) FROM checkout_counters_receiptverification WHERE verification_code = ?",
            (code,)
        )
        count = cursor.fetchone()[0]
        
        while count > 0:
            code = ''.join(random.choice(chars) for _ in range(8))
            cursor.execute(
                "SELECT COUNT(*) FROM checkout_counters_receiptverification WHERE verification_code = ?",
                (code,)
            )
            count = cursor.fetchone()[0]
        
        return code
