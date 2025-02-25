from django.core.management.base import BaseCommand
from django.db import connection
import random
import string
from django.utils import timezone

class Command(BaseCommand):
    help = 'Crea un código de verificación para un comprobante específico'

    def add_arguments(self, parser):
        parser.add_argument('receipt_id', type=int, help='ID del comprobante')

    def handle(self, *args, **options):
        receipt_id = options['receipt_id']
        
        with connection.cursor() as cursor:
            # Verificar si el comprobante existe
            cursor.execute("SELECT receipt_number FROM checkout_counters_receipt WHERE id = ?", (receipt_id,))
            receipt = cursor.fetchone()
            
            if not receipt:
                self.stdout.write(self.style.ERROR(f"No se encontró el comprobante con ID {receipt_id}"))
                return
            
            receipt_number = receipt[0]
            
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
                return
            
            # Generar un código alfanumérico único
            code = self.generate_verification_code(cursor)
            
            # Crear el código de verificación
            now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                cursor.execute(
                    """
                    INSERT INTO checkout_counters_receiptverification 
                    (verification_code, created_at, receipt_id) 
                    VALUES (?, ?, ?)
                    """,
                    (code, now, receipt_id)
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Código de verificación generado para el comprobante {receipt_number}: {code}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error al generar código de verificación: {str(e)}"
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
