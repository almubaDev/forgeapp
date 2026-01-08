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
    company_rut = models.CharField('RUT Empresa', max_length=12, blank=True)
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

class PaymentEvent(models.Model):
    """
    Modelo para eventos de pago de suscripciones.
    Representa pagos esperados que se generan automáticamente para cada período de suscripción.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
    ]

    subscription = models.ForeignKey(
        'Subscription',
        on_delete=models.CASCADE,
        related_name='payment_events',
        verbose_name='Suscripción'
    )
    expected_date = models.DateField('Fecha Esperada de Pago')
    paid_date = models.DateField('Fecha de Pago Real', null=True, blank=True)
    amount = models.DecimalField('Monto', max_digits=10, decimal_places=2)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Evento de Pago'
        verbose_name_plural = 'Eventos de Pago'
        ordering = ['-expected_date']

    def __str__(self):
        return f"Evento {self.subscription.reference_id} - {self.expected_date} ({self.get_status_display()})"

    def mark_as_paid(self, paid_date=None):
        """
        Marca el evento como pagado y actualiza la suscripción.
        Si auto_renewal está activo, se genera automáticamente el siguiente evento mediante signals.
        """
        from datetime import date
        from dateutil.relativedelta import relativedelta

        if self.status == 'paid':
            logger.warning(f"Evento {self.id} ya está marcado como pagado")
            return False

        # Si no se proporciona fecha de pago, usar hoy
        if paid_date is None:
            paid_date = date.today()

        self.status = 'paid'
        self.paid_date = paid_date
        self.save()

        # Actualizar start_date de la suscripción para reflejar el nuevo período
        subscription = self.subscription

        # Calcular nueva fecha de inicio basada en la fecha esperada de este evento
        # La nueva fecha de inicio es la fecha esperada de este pago
        subscription.start_date = self.expected_date
        subscription.save()

        logger.info(f"Evento {self.id} marcado como pagado. Suscripción {subscription.reference_id} actualizada")

        # El siguiente evento se genera automáticamente mediante signals si auto_renewal=True
        return True

class Subscription(models.Model):
    """Modelo para las suscripciones con máquina de estados"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('monthly', 'Mensual'),
        ('annual', 'Anual'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='subscriptions')
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_id = models.CharField('ID de Referencia', max_length=20, unique=True, default='TEMP000000')
    payment_type = models.CharField('Tipo de Pago', max_length=20, choices=PAYMENT_TYPE_CHOICES, default='monthly')
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
    start_date = models.DateField('Fecha de Inicio', null=True, blank=True)
    auto_renewal = models.BooleanField('Autorenovación', default=True)
    renewal_notes = models.TextField('Notas de Renovación', blank=True)
    cancelled_at = models.DateField('Fecha de Cancelación', null=True, blank=True)
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

    @property
    def current_period_end(self):
        """
        Calcula dinámicamente la fecha de renovación basándose en start_date y payment_type.
        Esta es la fecha esperada del próximo pago.
        Retorna None si la suscripción no tiene fecha de inicio (está en PENDING).
        """
        from dateutil.relativedelta import relativedelta

        if not self.start_date:
            return None

        if self.payment_type == 'monthly':
            return self.start_date + relativedelta(months=1)
        else:  # annual
            return self.start_date + relativedelta(years=1)

    @property
    def grace_period_end(self):
        """
        Calcula la fecha de fin del período de gracia (15 días después de current_period_end).
        Solo después de esta fecha la suscripción se marca como EXPIRED.
        Retorna None si la suscripción no tiene fecha de inicio (está en PENDING).
        """
        from dateutil.relativedelta import relativedelta

        if not self.current_period_end:
            return None

        return self.current_period_end + relativedelta(days=15)

    @property
    def is_expired(self):
        """
        Verifica si la suscripción ha expirado (pasó el período de gracia de 15 días).
        Retorna False si la suscripción no tiene fecha de inicio (está en PENDING).
        """
        from datetime import date

        if not self.grace_period_end:
            return False

        today = date.today()
        return self.status == 'active' and today > self.grace_period_end

    @property
    def days_until_renewal(self):
        """
        Días hasta la próxima renovación.
        Retorna None si la suscripción no tiene fecha de inicio (está en PENDING).
        """
        from datetime import date

        if not self.current_period_end:
            return None

        today = date.today()
        delta = self.current_period_end - today
        return delta.days

    @property
    def days_in_grace_period(self):
        """
        Días restantes en el período de gracia (si está en gracia).
        Retorna None si la suscripción no tiene fecha de inicio (está en PENDING).
        """
        from datetime import date

        if not self.current_period_end or not self.grace_period_end:
            return None

        today = date.today()

        if today <= self.current_period_end:
            return None  # No está en período de gracia

        if today > self.grace_period_end:
            return 0  # Período de gracia expirado

        delta = self.grace_period_end - today
        return delta.days

    def activate(self):
        """
        Activa la suscripción y genera el primer evento de pago.
        Actualiza la fecha de inicio al día actual.
        Transición: PENDING -> ACTIVE
        """
        from datetime import date

        if self.status != 'pending':
            logger.warning(f"Intentando activar suscripción {self.reference_id} que no está en estado PENDING")
            return False

        # Actualizar fecha de inicio al día actual
        self.start_date = date.today()
        self.status = 'active'
        self.save()

        # El evento de pago se genera automáticamente mediante signals
        logger.info(f"Suscripción {self.reference_id} activada exitosamente con fecha de inicio {self.start_date}")
        return True

    def deactivate(self):
        """
        Desactiva la suscripción y elimina eventos de pago pendientes.
        Transición: ACTIVE/EXPIRED -> INACTIVE
        """
        if self.status not in ['active', 'expired']:
            logger.warning(f"Intentando desactivar suscripción {self.reference_id} desde estado {self.status}")
            return False

        # Eliminar eventos de pago pendientes
        pending_events = self.payment_events.filter(status='pending')
        count = pending_events.count()
        pending_events.delete()

        self.status = 'inactive'
        self.save()

        logger.info(f"Suscripción {self.reference_id} desactivada. Eliminados {count} eventos pendientes")
        return True

    def cancel(self):
        """
        Cancela la suscripción y elimina eventos de pago pendientes.
        Transición: ACTIVE/INACTIVE/EXPIRED -> CANCELLED
        """
        if self.status == 'cancelled':
            logger.warning(f"Suscripción {self.reference_id} ya está cancelada")
            return False

        # Eliminar eventos de pago pendientes
        pending_events = self.payment_events.filter(status='pending')
        count = pending_events.count()
        pending_events.delete()

        self.status = 'cancelled'
        self.cancelled_at = timezone.now().date()
        self.save()

        logger.info(f"Suscripción {self.reference_id} cancelada. Eliminados {count} eventos pendientes")
        return True

    def renew(self):
        """
        Renueva la suscripción actualizando start_date al momento actual y generando nuevo evento.
        Se usa cuando se reactiva una suscripción INACTIVE o CANCELLED.
        """
        if self.status not in ['inactive', 'cancelled', 'expired']:
            logger.warning(f"Intentando renovar suscripción {self.reference_id} desde estado {self.status}")
            return False

        # Actualizar fecha de inicio al día actual
        from datetime import date
        self.start_date = date.today()
        self.status = 'active'
        self.cancelled_at = None
        self.save()

        # El evento de pago se genera automáticamente mediante signals
        logger.info(f"Suscripción {self.reference_id} renovada exitosamente con nueva fecha de inicio")
        return True
    
class Calculadora(models.Model):
    CURRENCY_CHOICES = [
        ('CLP', 'Pesos Chilenos (CLP)'),
        ('USD', 'Dólares (USD)'),
    ]

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
    currency = models.CharField('Moneda', max_length=3, choices=CURRENCY_CHOICES, default='CLP')
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

    def format_price(self, value):
        """Formatea un valor según la moneda de la calculadora"""
        if value is None:
            return "0"
        price_int = int(value)
        if self.currency == 'USD':
            # Formato USD: USD$12,000
            formatted = f"{price_int:,}".replace(",", ",")
            return f"USD${formatted}"
        else:
            # Formato CLP: CLP$12.000
            formatted = f"{price_int:,}".replace(",", ".")
            return f"CLP${formatted}"

    def get_formatted_subtotal(self):
        """Retorna el subtotal formateado según la moneda"""
        return self.format_price(self.subtotal)

    def get_formatted_total_anual(self):
        """Retorna el total anual formateado según la moneda"""
        return self.format_price(self.total_anual)

    def get_formatted_cuota_mensual(self):
        """Retorna la cuota mensual formateada según la moneda"""
        return self.format_price(self.cuota_mensual)

    def get_formatted_costo_mercado(self):
        """Retorna el costo de mercado formateado según la moneda"""
        return self.format_price(self.costo_mercado)

    def generar_suscripciones(self, subscription_type='both', auto_renewal=False):
        """
        Genera o actualiza suscripciones basadas en la calculadora.
        Las suscripciones se crean en estado PENDING sin fecha de inicio.
        La fecha de inicio se asigna cuando se activan.

        Args:
            subscription_type: 'monthly', 'annual', o 'both'
            auto_renewal: Si se habilita la renovación automática
        """
        from datetime import date

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

        # Buscar suscripciones existentes
        sub_mensual = self.subscriptions.filter(payment_type='monthly').first()
        sub_anual = self.subscriptions.filter(payment_type='annual').first()

        # Crear/actualizar suscripción mensual si se solicita
        if subscription_type in ['monthly', 'both']:
            if sub_mensual:
                # Actualizar suscripción existente
                sub_mensual.price = self.cuota_mensual
                sub_mensual.items_detail = items_json
                sub_mensual.auto_renewal = auto_renewal
                sub_mensual.save()
            else:
                # Crear nueva suscripción PENDING sin fecha de inicio
                sub_mensual = Subscription(
                    client=self.client,
                    application=self.application,
                    payment_type='monthly',
                    price=self.cuota_mensual,
                    start_date=None,  # Sin fecha de inicio, se asigna al activar
                    status='pending',
                    auto_renewal=auto_renewal,
                    items_detail=items_json,
                    calculadora=self,
                    renewal_notes=f"Generado desde calculadora: {self.nombre}"
                )
                sub_mensual.reference_id = Subscription.generate_reference_id('monthly')
                sub_mensual.save()

        # Crear/actualizar suscripción anual si se solicita
        if subscription_type in ['annual', 'both']:
            if sub_anual:
                # Actualizar suscripción existente
                sub_anual.price = self.total_anual
                sub_anual.items_detail = items_json
                sub_anual.auto_renewal = auto_renewal
                sub_anual.save()
            else:
                # Crear nueva suscripción PENDING sin fecha de inicio
                sub_anual = Subscription(
                    client=self.client,
                    application=self.application,
                    payment_type='annual',
                    price=self.total_anual,
                    start_date=None,  # Sin fecha de inicio, se asigna al activar
                    status='pending',
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

    def get_formatted_precio_unitario(self):
        """Retorna el precio unitario formateado según la moneda de la calculadora"""
        return self.calculadora.format_price(self.precio_unitario)

    def get_formatted_subtotal(self):
        """Retorna el subtotal formateado según la moneda de la calculadora"""
        return self.calculadora.format_price(self.subtotal)

    def save(self, *args, **kwargs):
        # Calcular subtotal del item
        self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal('1'), rounding=ROUND_UP)
        super().save(*args, **kwargs)
        
        # Actualizar totales de la calculadora
        self.calculadora.save()

class ServiceContractToken(models.Model):
    """Modelo para almacenar tokens de contratos de servicio"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente de Firma'),
        ('signed', 'Firmado'),
        ('expired', 'Expirado'),
    ]

    CURRENCY_CHOICES = [
        ('CLP', 'Pesos Chilenos (CLP)'),
        ('USD', 'Dólares (USD)'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contract_tokens')
    application_id = models.IntegerField('ID de Aplicación')
    subscription_type = models.CharField('Tipo de Suscripción', max_length=20, choices=Subscription.PAYMENT_TYPE_CHOICES)
    token = models.CharField('Token', max_length=100, unique=True)
    authorization_code = models.CharField('Código de Autorización', max_length=8, blank=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    expires_at = models.DateTimeField('Fecha de Expiración')
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    used = models.BooleanField('Usado', default=False)
    used_at = models.DateTimeField('Fecha de Uso', null=True, blank=True)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField('Moneda', max_length=3, choices=CURRENCY_CHOICES, default='CLP')

    # Datos de firma del cliente
    signed_rut = models.CharField('RUT Firmante', max_length=12, blank=True)
    signed_name = models.CharField('Nombre Firmante', max_length=200, blank=True)
    signed_at = models.DateTimeField('Fecha de Firma', null=True, blank=True)

    # PDF del contrato firmado
    signed_pdf = models.FileField('PDF Firmado', upload_to='contracts/signed/', null=True, blank=True)

    class Meta:
        verbose_name = 'Token de Contrato'
        verbose_name_plural = 'Tokens de Contratos'
        ordering = ['-created_at']

    def __str__(self):
        return f"Token para {self.client.name} - {self.token[:8]}..."

    @staticmethod
    def generate_authorization_code():
        """Genera un código de autorización único de 8 caracteres alfanuméricos"""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=8))

    def save(self, *args, **kwargs):
        # Generar código de autorización si no existe
        if not self.authorization_code:
            self.authorization_code = self.generate_authorization_code()
        super().save(*args, **kwargs)

    def is_expired(self):
        """Verifica si el token ha expirado"""
        return self.expires_at < timezone.now()

    def is_valid(self):
        """Verifica si el token es válido (no expirado y no usado)"""
        return not self.used and not self.is_expired()

    def get_public_url(self):
        """Retorna la URL pública para firmar el contrato"""
        from django.urls import reverse
        return reverse('forgeapp:public_contract', kwargs={'token': self.token})

    def get_formatted_price(self):
        """Retorna el precio formateado según la moneda"""
        if self.price is None:
            return "0"

        price_int = int(self.price)

        if self.currency == 'USD':
            # Formato USD: USD$12,000
            formatted = f"{price_int:,}".replace(",", ",")
            return f"USD${formatted}"
        else:
            # Formato CLP: CLP$12.000
            formatted = f"{price_int:,}".replace(",", ".")
            return f"CLP${formatted}"


class Appointment(models.Model):
    """Modelo para citas/reuniones en la agenda"""
    STATUS_CHOICES = [
        ('scheduled', 'Agendada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]

    date = models.DateField('Fecha')
    start_time = models.TimeField('Hora de Inicio')
    end_time = models.TimeField('Hora de Fin')
    name = models.CharField('Nombre del Cliente', max_length=200)
    email = models.EmailField('Correo Electrónico')
    description = models.TextField('Descripción', blank=True)
    meeting_link = models.URLField('Link de Reunión', max_length=500, blank=True)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='scheduled')
    is_blocked = models.BooleanField('Bloqueado', default=False, help_text='Horario bloqueado manualmente')
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.name} - {self.date} {self.start_time.strftime('%H:%M')}"

    @classmethod
    def get_default_blocked_slots(cls):
        """Retorna los slots bloqueados por defecto (00:00-08:00 y 20:00-23:00)
        Horario laboral: 9:00 a 20:00 - Slots de 1 hora
        """
        from datetime import time
        blocked = []
        # Bloqueados de 00:00 a 08:00 (antes de las 9:00)
        for hour in range(0, 9):
            blocked.append(time(hour, 0))
        # Bloqueados de 20:00 a 23:00 (después de las 20:00)
        for hour in range(20, 24):
            blocked.append(time(hour, 0))
        return blocked

    @classmethod
    def is_slot_available(cls, date, start_time):
        """Verifica si un slot está disponible"""
        from datetime import time as time_type, timedelta, datetime as dt

        # Calcular hora de fin (1 hora después)
        start_dt = dt.combine(date, start_time)
        end_dt = start_dt + timedelta(minutes=60)
        end_time = end_dt.time()

        # Verificar si hay citas o bloqueos que se solapan
        overlapping = cls.objects.filter(
            date=date,
            status='scheduled'
        ).filter(
            models.Q(start_time__lt=end_time, end_time__gt=start_time)
        ).exists()

        if overlapping:
            return False

        # Verificar si está en horario bloqueado por defecto
        default_blocked = cls.get_default_blocked_slots()
        is_default_blocked = start_time in default_blocked

        # Si está bloqueado por defecto, verificar si fue habilitado manualmente
        if is_default_blocked:
            manually_enabled = cls.objects.filter(
                date=date,
                start_time=start_time,
                status='cancelled',
                is_blocked=False
            ).exists()
            return manually_enabled

        return True

    @classmethod
    def get_appointments_for_date(cls, date):
        """Retorna todas las citas para una fecha específica"""
        return cls.objects.filter(date=date, status='scheduled')


class ContactMessage(models.Model):
    """Modelo para almacenar mensajes del formulario de contacto"""
    STATUS_CHOICES = [
        ('new', 'Nuevo'),
        ('read', 'Leído'),
        ('archived', 'Archivado'),
    ]

    name = models.CharField('Nombre', max_length=200)
    email = models.EmailField('Correo Electrónico')
    message = models.TextField('Mensaje')
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('Fecha de Recepción', auto_now_add=True)
    read_at = models.DateTimeField('Fecha de Lectura', null=True, blank=True)
    archived_at = models.DateTimeField('Fecha de Archivo', null=True, blank=True)
    notes = models.TextField('Notas internas', blank=True)
    # Campos para la cita agendada
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_message',
        verbose_name='Cita Agendada'
    )
    meeting_link = models.URLField('Link de Reunión', max_length=500, blank=True)

    class Meta:
        verbose_name = 'Mensaje de Contacto'
        verbose_name_plural = 'Mensajes de Contacto'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email} ({self.get_status_display()})"

    def mark_as_read(self):
        """Marca el mensaje como leído"""
        if self.status == 'new':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()

    def archive(self):
        """Archiva el mensaje"""
        self.status = 'archived'
        self.archived_at = timezone.now()
        self.save()

    def unarchive(self):
        """Desarchiva el mensaje"""
        self.status = 'read'
        self.archived_at = None
        self.save()

