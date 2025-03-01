# forgeapp/models.py
import logging
import base64
import re
import os
import json
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal, ROUND_UP
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.validators import MinValueValidator
from cryptography.fernet import Fernet
from datetime import datetime, timedelta

logger = logging.getLogger('forgeapp')

def get_encryption_key():
    """Obtiene o genera una clave de encriptación"""
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    if key is None:
        key = base64.urlsafe_b64encode(os.urandom(32))
        setattr(settings, 'ENCRYPTION_KEY', key)
    return key

class ApplicationConfig(models.Model):
    """Modelo para almacenar configuraciones de aplicaciones"""
    FIELD_TYPES = [
        ('text', 'Texto'),
        ('number', 'Número'),
        ('url', 'URL'),
        ('password', 'Contraseña'),
    ]

    application = models.ForeignKey(
        'Application',
        on_delete=models.CASCADE,
        related_name='configs',
        verbose_name='Aplicación'
    )
    key = models.CharField('Clave', max_length=100)
    value = models.TextField('Valor')
    field_type = models.CharField(
        'Tipo de Campo',
        max_length=20,
        choices=FIELD_TYPES,
        default='text'
    )
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)
    description = models.TextField('Descripción', blank=True)
    is_encrypted = models.BooleanField('Está Encriptado', default=False)

    class Meta:
        verbose_name = 'Configuración de Aplicación'
        verbose_name_plural = 'Configuraciones de Aplicación'
        unique_together = ['application', 'key']
        ordering = ['key']

    def __str__(self):
        return f"{self.application.name} - {self.key}"

    def encrypt_value(self, value):
        """Encripta un valor usando Fernet"""
        if not value:
            return value
        f = Fernet(get_encryption_key())
        return f.encrypt(value.encode()).decode()

    def decrypt_value(self, encrypted_value):
        """Desencripta un valor usando Fernet"""
        if not encrypted_value:
            return encrypted_value
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_value.encode()).decode()

    def save(self, *args, **kwargs):
        # Encriptar contraseñas antes de guardar
        if self.field_type == 'password' and not self.is_encrypted:
            self.value = self.encrypt_value(self.value)
            self.is_encrypted = True
        super().save(*args, **kwargs)

    def get_value(self):
        """Obtiene el valor, desencriptando si es necesario"""
        if self.field_type == 'password' and self.is_encrypted:
            return self.decrypt_value(self.value)
        elif self.field_type == 'number':
            try:
                return float(self.value)
            except (ValueError, TypeError):
                return None
        return self.value

def validate_rut(value):
    """Valida el formato del RUT chileno (12345678-9)"""
    if not re.match(r'^\d{7,8}-[\dkK]$', value):
        raise ValidationError('El RUT debe tener el formato 12345678-9')

class Client(models.Model):
    """Modelo para los clientes"""
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('pending', 'Pendiente'),
    ]

    NATIONALITY_CHOICES = [
        ('chilena', 'Chilena'),
        ('extranjera', 'Extranjera'),
    ]
    
    CONTRACT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
        ('none', 'Sin Contrato'),
    ]

    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validate_rut])
    first_name = models.CharField('Nombres', max_length=100, default='')
    last_name = models.CharField('Apellidos', max_length=100, default='')
    name = models.CharField('Nombre Completo', max_length=200, editable=False)
    email = models.EmailField('Correo Electrónico')
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    company = models.CharField('Empresa', max_length=200, blank=True)
    company_rut = models.CharField('RUT Empresa', max_length=12, blank=True, validators=[validate_rut])
    position = models.CharField('Cargo', max_length=100, blank=True)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='active')
    nationality = models.CharField('Nacionalidad', max_length=20, choices=NATIONALITY_CHOICES, default='chilena')
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Fecha de Registro', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)
    accept_marketing = models.BooleanField('Acepta Marketing', default=False)
    contract_status = models.CharField('Estado del Contrato', max_length=20, choices=CONTRACT_STATUS_CHOICES, default='none')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Actualizar el campo name a partir de first_name y last_name
        self.name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Application(models.Model):
    name = models.CharField('Nombre', max_length=200)
    description = models.TextField('Descripción')
    url = models.URLField('URL del Proyecto')
    documentation_url = models.URLField('URL de Documentación', blank=True, null=True)
    git_repository = models.URLField('Repositorio Git', blank=True, null=True)
    owner = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_applications',
        verbose_name='Propietario'
    )
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)
    class Meta:
        verbose_name = 'Aplicación'
        verbose_name_plural = 'Aplicaciones'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Payment(models.Model):
    """Modelo para registrar pagos de suscripciones"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('failed', 'Fallido'),
    ]

    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='forgeapp_payments')
    amount = models.DecimalField('Monto', max_digits=10, decimal_places=2)
    payment_date = models.DateField('Fecha de Pago')
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField('Referencia', max_length=100, blank=True)
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Pago {self.reference} - {self.subscription.reference_id}"

    def complete_payment(self):
        """Marca el pago como completado y actualiza las fechas de la suscripción"""
        self.status = 'completed'
        self.save()
        
        # Actualizar la suscripción
        self.subscription.last_payment_date = self.payment_date
        self.subscription.update_payment_dates()
        
        return True

class Subscription(models.Model):
    """Modelo para las suscripciones"""
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
        ('pending', 'Pendiente'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('monthly', 'Mensual'),
        ('annual', 'Anual'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='subscriptions')
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='inactive')
    reference_id = models.CharField('ID de Referencia', max_length=20, unique=True, default='TEMP000000')
    payment_type = models.CharField('Tipo de Pago', max_length=20, choices=PAYMENT_TYPE_CHOICES, default='monthly')
    next_payment_date = models.DateField('Fecha Próximo Pago', null=True, blank=True)
    last_payment_date = models.DateField('Fecha Último Pago', null=True, blank=True)
    accept_marketing = models.BooleanField('Acepta Marketing', default=False)

    @staticmethod
    def generate_reference_id(payment_type, attempt=0):
        """Genera un ID de referencia único basado en el tipo de pago"""
        prefix = 'AN' if payment_type == 'annual' else 'ME'
        
        # Si es un reintento por colisión, usar un número aleatorio
        if attempt > 0:
            import random
            new_num = random.randint(1, 999999)
        else:
            # Obtener el último ID con este prefijo
            last_sub = Subscription.objects.filter(
                reference_id__startswith=prefix
            ).order_by('-reference_id').first()
            
            if last_sub:
                try:
                    # Extraer el número del último ID
                    last_num = int(last_sub.reference_id[2:])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
        
        # Formatear el nuevo ID (prefijo + 6 dígitos)
        reference_id = f"{prefix}{new_num:06d}"
        
        # Verificar que sea único
        if Subscription.objects.filter(reference_id=reference_id).exists():
            if attempt < 3:  # Máximo 3 intentos
                return Subscription.generate_reference_id(payment_type, attempt + 1)
            raise ValueError("No se pudo generar un ID único después de múltiples intentos")
            
        return reference_id

    def save(self, *args, **kwargs):
        """Sobreescribe el método save para asegurar reference_id único"""
        if not self.reference_id or self.reference_id == 'TEMP000000':
            max_attempts = 3
            attempt = 0
            while attempt < max_attempts:
                try:
                    self.reference_id = self.generate_reference_id(self.payment_type)
                    super().save(*args, **kwargs)
                    return
                except Exception as e:
                    attempt += 1
                    if attempt == max_attempts:
                        raise ValueError("No se pudo guardar con un ID único después de múltiples intentos")
        else:
            super().save(*args, **kwargs)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2, validators=[
        MinValueValidator(1, message='El precio debe ser mayor a 0')
    ])
    start_date = models.DateField('Fecha de Inicio')
    end_date = models.DateField('Fecha de Fin')
    auto_renewal = models.BooleanField('Autorenovación', default=False)
    renewal_notes = models.TextField('Notas de Renovación', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Campos para detalles de items
    items_detail = models.JSONField('Detalles de Items', default=dict, blank=True)
    calculadora = models.ForeignKey(
        'Calculadora', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='subscriptions'
    )

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client.name} - {self.application.name} ({self.get_payment_type_display()})"
    
    def has_pending_payment(self):
        """Verifica si hay pagos pendientes para esta suscripción"""
        return self.forgeapp_payments.filter(status='pending').exists()

    def can_register_payment(self):
        """Verifica si se puede registrar un nuevo pago"""
        return self.status == 'active'
        
    def register_payment(self, amount=None, payment_date=None, notes=''):
        """
        Registra un nuevo pago para la suscripción.
        """
        if amount is None:
            amount = self.price
            
        if payment_date is None:
            payment_date = timezone.now().date()
            
        # Crear un nuevo pago
        payment = Payment.objects.create(
            subscription=self,
            amount=amount,
            payment_date=payment_date,
            status='completed',
            reference=f"PAY-{self.reference_id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            notes=notes
        )
        
        # Actualizar fechas de la suscripción
        self.last_payment_date = payment_date
        self.update_payment_dates()
        self.status = 'active'  # Asegurar que la suscripción esté activa después del pago
        self.save()
        
        return payment

    def update_payment_dates(self):
        """Actualiza las fechas de pago basado en el último pago"""
        today = timezone.now().date()
        self.last_payment_date = today
        
        # Calcular próxima fecha de pago
        if self.payment_type == 'monthly':
            # Si es mensual, el próximo pago es en un mes
            # Usar la fecha de inicio como referencia para mantener el mismo día del mes
            reference_date = self.start_date
            if self.last_payment_date:
                # Si ya hubo un pago, usar esa fecha como referencia
                reference_date = self.last_payment_date
            
            # Calcular próxima fecha manteniendo el mismo día del mes
            # Crear una nueva fecha con el mismo día pero el mes siguiente
            next_month = reference_date.month + 1
            next_year = reference_date.year
            
            # Si el mes es diciembre, avanzar al año siguiente
            if next_month > 12:
                next_month = 1
                next_year += 1
            
            # Obtener el último día del próximo mes
            last_day = self._last_day_of_month(next_year, next_month)
            
            # Asegurarse de que el día no exceda el último día del mes
            next_day = min(reference_date.day, last_day)
            
            # Crear la fecha del próximo pago
            next_date = datetime(next_year, next_month, next_day).date()
            
            # Si la fecha calculada ya pasó, avanzar otro mes
            if next_date <= today:
                next_month = next_date.month + 1
                next_year = next_date.year
                
                # Si el mes es diciembre, avanzar al año siguiente
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                
                # Obtener el último día del próximo mes
                last_day = self._last_day_of_month(next_year, next_month)
                
                # Asegurarse de que el día no exceda el último día del mes
                next_day = min(reference_date.day, last_day)
                
                # Crear la fecha del próximo pago
                next_date = datetime(next_year, next_month, next_day).date()
            
            self.next_payment_date = next_date
        else:
            # Si es anual, el próximo pago es en un año
            # Usar la fecha de inicio como referencia para mantener el mismo día del año
            reference_date = self.start_date
            if self.last_payment_date:
                # Si ya hubo un pago, usar esa fecha como referencia
                reference_date = self.last_payment_date
            
            # Calcular próxima fecha manteniendo el mismo día del año
            next_year = reference_date.year + 1
            
            # Intentar mantener el mismo día del año que la fecha de inicio
            try:
                next_date = datetime(next_year, reference_date.month, reference_date.day).date()
            except ValueError:
                # En caso de 29 de febrero en año no bisiesto
                if reference_date.month == 2 and reference_date.day == 29:
                    next_date = datetime(next_year, 2, 28).date()
                else:
                    # Otro error, usar el último día del mes
                    last_day = self._last_day_of_month(next_year, reference_date.month)
                    next_date = datetime(next_year, reference_date.month, last_day).date()
            
            # Si la fecha calculada ya pasó, avanzar otro año
            if next_date <= today:
                next_year = next_date.year + 1
                
                # Intentar mantener el mismo día del año que la fecha de inicio
                try:
                    next_date = datetime(next_year, reference_date.month, reference_date.day).date()
                except ValueError:
                    # En caso de 29 de febrero en año no bisiesto
                    if reference_date.month == 2 and reference_date.day == 29:
                        next_date = datetime(next_year, 2, 28).date()
                    else:
                        # Otro error, usar el último día del mes
                        last_day = self._last_day_of_month(next_year, reference_date.month)
                        next_date = datetime(next_year, reference_date.month, last_day).date()
            
            self.next_payment_date = next_date
        
        logger.info(f"Fechas de pago actualizadas para suscripción {self.reference_id}: último={self.last_payment_date}, próximo={self.next_payment_date}")
        self.save()
    
    def _last_day_of_month(self, year, month):
        """Retorna el último día del mes especificado"""
        import calendar
        return calendar.monthrange(year, month)[1]
    
class Calculadora(models.Model):
    nombre = models.CharField('Nombre/Referencia', max_length=200)
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='calculadoras',
        verbose_name='Cliente'
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calculadoras',
        verbose_name='Aplicación'
    )
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    subtotal = models.DecimalField('Suma Total de Items', max_digits=10, decimal_places=2, default=0)
    margen = models.DecimalField('Margen de Ganancia', max_digits=5, decimal_places=2, default=0)
    descuento = models.DecimalField('Descuento por Pago Anual', max_digits=5, decimal_places=2, default=0)
    total_anual = models.DecimalField('Total Anual con Descuento', max_digits=10, decimal_places=2, default=0)
    cuota_mensual = models.DecimalField('Valor Cuota Mensual', max_digits=10, decimal_places=2, default=0)
    notas = models.TextField('Notas', blank=True)
    costo_mercado = models.DecimalField(
        'Costo promedio en el mercado',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Costo promedio de desarrollo de la aplicación en el mercado'
    )
    tiempo_mercado = models.DecimalField(
        'Tiempo promedio en el mercado (semanas)',
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Tiempo promedio de desarrollo en el mercado en semanas'
    )

    class Meta:
        verbose_name = 'Calculadora'
        verbose_name_plural = 'Calculadoras'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nombre} - {self.client.name}"
        
    def recalcular_totales(self):
        """Recalcula todos los totales basados en los items y porcentajes"""
        # Calcular subtotal sumando todos los items
        self.subtotal = sum(item.subtotal for item in self.items.all())
        
        # Total con margen
        total_con_margen = (self.subtotal * (1 + self.margen / 100)).quantize(Decimal('1'), rounding=ROUND_UP)
        
        # Cuota mensual (sin descuento)
        self.cuota_mensual = (total_con_margen / 12).quantize(Decimal('1'), rounding=ROUND_UP)
        
        # Total anual con descuento
        self.total_anual = (total_con_margen * (1 - self.descuento / 100)).quantize(Decimal('1'), rounding=ROUND_UP)

    def save(self, *args, **kwargs):
        # Solo recalcular totales si la instancia ya existe (tiene ID)
        if self.pk:
            self.recalcular_totales()
        super().save(*args, **kwargs)

    def generar_suscripciones(self, start_date, auto_renewal=False):
        """
        Genera o actualiza suscripciones basadas en la calculadora.
        Solo crea nuevas suscripciones si no existen.
        """
        # Preparar detalles de items
        items_json = {
            'items': [
                {
                    'descripcion': item.descripcion,
                    'cantidad': str(item.cantidad),
                    'precio_unitario': str(item.precio_unitario),
                    'subtotal': str(item.subtotal)
                }
                for item in self.items.all()
            ],
            'margen': str(self.margen),
            'descuento_anual': str(self.descuento)
        }

        # Calcular fecha fin (1 año después)
        from datetime import date, timedelta
        end_date = start_date + timedelta(days=365)

        # Buscar suscripciones existentes
        sub_mensual = self.subscriptions.filter(payment_type='monthly').first()
        sub_anual = self.subscriptions.filter(payment_type='annual').first()

        # Actualizar o crear suscripción mensual
        if sub_mensual:
            # Actualizar suscripción existente
            sub_mensual.price = self.cuota_mensual
            sub_mensual.items_detail = items_json
            sub_mensual.auto_renewal = auto_renewal
            sub_mensual.save()
        elif not self.subscriptions.filter(payment_type='monthly').exists():
            # Crear nueva suscripción solo si no existe ninguna mensual
            sub_mensual = Subscription(
                client=self.client,
                application=self.application,
                payment_type='monthly',
                price=self.cuota_mensual,
                start_date=start_date,
                end_date=end_date,
                auto_renewal=auto_renewal,
                items_detail=items_json,
                calculadora=self,
                renewal_notes=f"Generado desde calculadora: {self.nombre}"
            )
            sub_mensual.reference_id = Subscription.generate_reference_id('monthly')
            sub_mensual.save()

        # Actualizar o crear suscripción anual
        if sub_anual:
            # Actualizar suscripción existente
            sub_anual.price = self.total_anual
            sub_anual.items_detail = items_json
            sub_anual.auto_renewal = auto_renewal
            sub_anual.save()
        elif not self.subscriptions.filter(payment_type='annual').exists():
            # Crear nueva suscripción solo si no existe ninguna anual
            sub_anual = Subscription(
                client=self.client,
                application=self.application,
                payment_type='annual',
                price=self.total_anual,
                start_date=start_date,
                end_date=end_date,
                auto_renewal=auto_renewal,
                items_detail=items_json,
                calculadora=self,
                renewal_notes=f"Generado desde calculadora: {self.nombre}"
            )
            sub_anual.reference_id = Subscription.generate_reference_id('annual')
            sub_anual.save()

        return sub_mensual, sub_anual

class ItemCalculo(models.Model):
    calculadora = models.ForeignKey(Calculadora, on_delete=models.CASCADE, related_name='items')
    descripcion = models.CharField('Descripción', max_length=200)
    cantidad = models.DecimalField('Cantidad', max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField('Precio Unitario', max_digits=10, decimal_places=2)
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item de Cálculo'
        verbose_name_plural = 'Items de Cálculo'

    def __str__(self):
        return f"{self.descripcion} - {self.calculadora.nombre}"

    def save(self, *args, **kwargs):
        # Calcular subtotal del item
        self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal('1'), rounding=ROUND_UP)
        super().save(*args, **kwargs)
        
        # Actualizar totales de la calculadora
        self.calculadora.save()

class ServiceContractToken(models.Model):
    """Modelo para almacenar tokens de contratos de servicio"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contract_tokens')
    application_id = models.IntegerField('ID de Aplicación')
    subscription_type = models.CharField('Tipo de Suscripción', max_length=20, choices=Subscription.PAYMENT_TYPE_CHOICES)
    token = models.CharField('Token', max_length=100, unique=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    expires_at = models.DateTimeField('Fecha de Expiración')
    used = models.BooleanField('Usado', default=False)
    used_at = models.DateTimeField('Fecha de Uso', null=True, blank=True)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Token de Contrato'
        verbose_name_plural = 'Tokens de Contratos'
        ordering = ['-created_at']

    def __str__(self):
        return f"Token para {self.client.name} - {self.token[:8]}..."

    def is_expired(self):
        """Verifica si el token ha expirado"""
        return self.expires_at < timezone.now()

    def is_valid(self):
        """Verifica si el token es válido (no expirado y no usado)"""
        return not self.used and not self.is_expired()
            
            
