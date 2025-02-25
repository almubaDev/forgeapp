from django.db import models
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class PaymentLinkManager(models.Manager):
    def update_payment_status(self, reference_id, status, payment_data=None):
        """
        Actualiza el estado del pago y la suscripción asociada
        """
        try:
            payment_link = self.get(reference_id=reference_id)
            
            # Mapear estado de Mercado Pago a nuestro estado
            status_mapping = {
                "approved": "paid",
                "pending": "pending",
                "rejected": "cancelled"
            }
            
            new_status = status_mapping.get(status, "pending")
            payment_link.status = new_status
            payment_link.is_paid = status == "approved"
            
            # Si el pago fue aprobado, expirar el link inmediatamente
            if status == "approved":
                payment_link.expires_at = timezone.now()
                logger.info(f"Link de pago {reference_id} marcado como expirado después de pago exitoso")
            
            # Actualizar información del pagador si está disponible
            if payment_data:
                # Intentar obtener el email del pagador
                if "payer" in payment_data:
                    payment_link.payer_email = payment_data["payer"].get("email", "")
                    payer_name = payment_data["payer"].get("first_name", "")
                    if payment_data["payer"].get("last_name"):
                        payer_name += f" {payment_data['payer']['last_name']}"
                    payment_link.payer_name = payer_name
                # Si no está en payer, buscar en additional_info
                elif "additional_info" in payment_data and "payer" in payment_data["additional_info"]:
                    payer_info = payment_data["additional_info"]["payer"]
                    payment_link.payer_email = payer_info.get("email", "")
                    payment_link.payer_name = payer_info.get("first_name", "")
                    if payer_info.get("last_name"):
                        payment_link.payer_name += f" {payer_info['last_name']}"
            
            payment_link.save()
            
            # Si el pago fue aprobado, actualizar la suscripción
            if payment_link.is_paid and payment_link.subscription:
                logger.info(f"Actualizando fechas de pago para suscripción {payment_link.subscription.reference_id}")
                payment_link.subscription.update_payment_dates()
            
            return payment_link
            
        except self.model.DoesNotExist:
            logger.error(f"PaymentLink no encontrado: {reference_id}")
            return None
        except Exception as e:
            logger.error(f"Error actualizando estado de pago: {str(e)}")
            return None

class PaymentLink(models.Model):
    """Modelo para links de pago"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado'),
        ('expired', 'Expirado'),
    ]

    reference_id = models.CharField('ID de Referencia', max_length=100, unique=True)
    subscription = models.ForeignKey(
        'forgeapp.Subscription',
        on_delete=models.PROTECT,
        related_name='payment_links',
        verbose_name='Suscripción',
        null=True,
        blank=True
    )
    amount = models.DecimalField('Monto', max_digits=10, decimal_places=2)
    description = models.TextField('Descripción')
    payment_link = models.URLField('Link de Pago')
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    is_paid = models.BooleanField('Está Pagado', default=False)
    expires_at = models.DateTimeField('Expira en', null=True, blank=True)
    payer_email = models.EmailField('Email del Pagador', blank=True)
    payer_name = models.CharField('Nombre del Pagador', max_length=200, null=True, blank=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)

    objects = PaymentLinkManager()

    class Meta:
        verbose_name = 'Link de Pago'
        verbose_name_plural = 'Links de Pago'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_id} - {self.amount}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('checkout_counters:payment_detail', kwargs={'pk': self.pk})

    def get_detail_url(self):
        """URL para detalle usando reference_id"""
        from django.urls import reverse
        return reverse('checkout_counters:payment_detail_by_ref', kwargs={'reference_id': self.reference_id})

class Receipt(models.Model):
    """Modelo para comprobantes de pago"""
    payment_link = models.OneToOneField(
        PaymentLink,
        on_delete=models.PROTECT,
        related_name='receipt',
        verbose_name='Link de Pago'
    )
    receipt_number = models.CharField('Número de Comprobante', max_length=100, unique=True)
    secret_code = models.UUIDField('Código Secreto', default=uuid.uuid4, editable=False)
    mercadopago_id = models.CharField('ID de Mercado Pago', max_length=100, blank=True, null=True)
    pdf_file = models.FileField('Archivo PDF', upload_to='receipts/')
    generated_at = models.DateTimeField('Fecha de Generación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Comprobante'
        verbose_name_plural = 'Comprobantes'
        ordering = ['-generated_at']

    def __str__(self):
        return self.receipt_number
        
    def get_masked_rut(self, rut):
        """Enmascara el RUT mostrando solo los últimos 3 dígitos y el dígito verificador"""
        if not rut:
            return ''
        # Asumiendo formato 12345678-9
        parts = rut.split('-')
        if len(parts) != 2:
            return rut
        main_part = parts[0]
        verifier = parts[1]
        masked = 'X' * (len(main_part) - 3) + main_part[-3:] + '-' + verifier
        return masked

    def generate_receipt_number(self):
        """Genera el número de comprobante con el formato especificado"""
        try:
            # Obtener la suscripción y cliente desde el payment_link
            payment_link = self.payment_link
            subscription = payment_link.subscription
            client = subscription.client
            year = timezone.now().year
            
            # Obtener el último número de secuencia del año
            last_receipt = Receipt.objects.filter(
                receipt_number__contains=f'-{year}-'
            ).order_by('-receipt_number').first()
            
            if last_receipt:
                try:
                    last_sequence = int(last_receipt.receipt_number.split('-')[-1])
                    sequence = str(last_sequence + 1).zfill(4)
                except (ValueError, IndexError):
                    sequence = '0001'
            else:
                sequence = '0001'
            
            # Construir el número de comprobante
            receipt_number = f"REC-{self.payment_link.reference_id}-{subscription.reference_id}.{client.id}-{year}-{sequence}"
            return receipt_number
            
        except Exception as e:
            logger.error(f"Error generating receipt number: {str(e)}")
            # Fallback a un formato simple si hay error
            return f"REC-{self.payment_link.reference_id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)

class ReceiptVerification(models.Model):
    """Modelo para códigos de verificación de comprobantes"""
    receipt = models.OneToOneField(
        Receipt,
        on_delete=models.CASCADE,
        related_name='verification',
        verbose_name='Comprobante'
    )
    verification_code = models.CharField('Código de Verificación', max_length=20, unique=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    
    @staticmethod
    def generate_verification_code():
        """Genera un código alfanumérico único para verificación"""
        import random
        import string
        
        # Generar un código alfanumérico de 8 caracteres
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(chars) for _ in range(8))
        
        # Verificar que sea único
        while ReceiptVerification.objects.filter(verification_code=code).exists():
            code = ''.join(random.choice(chars) for _ in range(8))
            
        return code
    
    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = self.generate_verification_code()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Verificación de Comprobante'
        verbose_name_plural = 'Verificaciones de Comprobantes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verificación para {self.receipt.receipt_number}"
