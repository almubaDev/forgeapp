# forgeapp/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal, ROUND_UP
from django.core.exceptions import ValidationError
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import re
import os

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

    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validate_rut])
    name = models.CharField('Nombre', max_length=200)
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

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Application(models.Model):
    name = models.CharField('Nombre', max_length=200)
    description = models.TextField('Descripción')
    url = models.URLField('URL del Proyecto')
    documentation_url = models.URLField('URL de Documentación', blank=True, null=True)
    git_repository = models.URLField('Repositorio Git', blank=True, null=True)
    owner = models.ForeignKey(  # Añadimos este campo
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

class Subscription(models.Model):
    """Modelo para las suscripciones"""
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('cancelled', 'Cancelada'),
        ('pending', 'Pendiente'),
        ('expired', 'Expirada'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('monthly', 'Mensual'),
        ('annual', 'Anual'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='subscriptions')
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_type = models.CharField('Tipo de Pago', max_length=20, choices=PAYMENT_TYPE_CHOICES, default='monthly')
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    start_date = models.DateField('Fecha de Inicio')
    end_date = models.DateField('Fecha de Fin')
    auto_renewal = models.BooleanField('Autorenovación', default=False)
    renewal_notes = models.TextField('Notas de Renovación', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Campos para detalles de items
    items_detail = models.JSONField('Detalles de Items', default=dict, blank=True)
    original_calculator = models.ForeignKey(
        'Calculadora', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='generated_subscriptions'
    )

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client.name} - {self.application.name} ({self.get_payment_type_display()})"
    
    def has_pending_payment(self):
        """Verifica si hay pagos pendientes para esta suscripción"""
        return self.payments.filter(status='pending').exists()

    def can_register_payment(self):
        """Verifica si se puede registrar un nuevo pago"""
        return (
            self.status == 'active' and  # Suscripción activa
            not self.has_pending_payment() and  # No hay pagos pendientes
            self.end_date >= timezone.now().date()  # No está vencida
        )
    
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
        Genera dos suscripciones: una mensual y una anual
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

        # Crear suscripción mensual
        Subscription.objects.create(
            client=self.client,
            application=self.application,
            payment_type='monthly',
            price=self.cuota_mensual,
            start_date=start_date,
            end_date=end_date,
            auto_renewal=auto_renewal,
            items_detail=items_json,
            original_calculator=self,
            renewal_notes=f"Generado desde calculadora: {self.nombre}"
        )

        # Crear suscripción anual
        Subscription.objects.create(
            client=self.client,
            application=self.application,
            payment_type='annual',
            price=self.total_anual,
            start_date=start_date,
            end_date=end_date,
            auto_renewal=auto_renewal,
            items_detail=items_json,
            original_calculator=self,
            renewal_notes=f"Generado desde calculadora: {self.nombre}"
        )

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
