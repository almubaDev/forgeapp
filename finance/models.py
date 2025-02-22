from django.db import models
from django.utils import timezone

class PaymentMethod(models.Model):
    """Modelo para métodos de pago"""
    TYPE_CHOICES = [
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia'),
        ('card', 'Tarjeta'),
        ('other', 'Otro'),
    ]

    name = models.CharField('Nombre', max_length=100)
    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    is_active = models.BooleanField('Activo', default=True)
    config = models.JSONField('Configuración', blank=True, null=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'
        ordering = ['name']

    def __str__(self):
        return self.name

class Payment(models.Model):
    """Modelo para los pagos"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]

    subscription = models.ForeignKey(
        'forgeapp.Subscription', 
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Suscripción'
    )
    amount = models.DecimalField('Monto', max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField('Fecha de Pago', null=True, blank=True)
    due_date = models.DateField('Fecha de Vencimiento')
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        verbose_name='Método de Pago',
        null=True,
        blank=True
    )
    transaction_id = models.CharField('ID de Transacción', max_length=100, blank=True)
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pago {self.id} - {self.subscription.client.name}"

    @property
    def is_overdue(self):
        """Verifica si el pago está vencido"""
        return self.status == 'pending' and self.due_date < timezone.now().date()

class Receipt(models.Model):
    """Modelo para comprobantes de pago"""
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='receipt',
        verbose_name='Pago'
    )
    receipt_number = models.CharField('Número de Comprobante', max_length=100, unique=True)
    pdf_file = models.FileField('Archivo PDF', upload_to='receipts/')
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Comprobante'
        verbose_name_plural = 'Comprobantes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Comprobante {self.receipt_number}"

class Transaction(models.Model):
    """Modelo para las transacciones (ingresos/egresos)"""
    TYPE_CHOICES = [
        ('income', 'Ingreso'),
        ('expense', 'Egreso'),
    ]

    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    category = models.CharField('Categoría', max_length=100)
    description = models.TextField('Descripción')
    amount = models.DecimalField('Monto', max_digits=10, decimal_places=2)
    date = models.DateField('Fecha')
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Pago Relacionado'
    )
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_display()} - {self.description[:50]}"
