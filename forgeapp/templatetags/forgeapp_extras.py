from django import template
from decimal import Decimal, InvalidOperation, ROUND_UP
from django.db import models
import locale

register = template.Library()

@register.filter
def add(value, arg):
    """Suma el argumento al valor"""
    try:
        if isinstance(value, str):
            value = Decimal(value)
        if isinstance(arg, str):
            arg = Decimal(arg)
        return value + arg
    except (ValueError, TypeError, InvalidOperation):
        return value

@register.filter
def formato_cl(value, client=None):
    """
    Formatea un número según la nacionalidad del cliente:
    - Cliente chileno: estilo chileno (1.234.567)
    - Cliente extranjero: estilo internacional (1,234,567.00)
    
    Args:
        value: Número a formatear
        client: Instancia de Cliente con atributo nationality
    
    Returns:
        str: Número formateado según nacionalidad
    """
    try:
        # Manejo de valores nulos o vacíos
        if value is None or value == '':
            return "0"
            
        # Convertir a Decimal para manejo preciso
        value = Decimal(str(value))
        
        # Determinar formato basado en nacionalidad
        is_chilean = not client or getattr(client, 'nationality', 'chilena') == 'chilena'
        
        if is_chilean:
            # Formato chileno: redondear a entero y usar puntos como separador de miles
            value = value.quantize(Decimal('1'), rounding=ROUND_UP)
            return f"{value:,.0f}".replace(",", ".")
        else:
            # Formato internacional: dos decimales y comas como separador de miles
            value = value.quantize(Decimal('0.01'), rounding=ROUND_UP)
            return f"{value:,.2f}"
            
    except (ValueError, TypeError, InvalidOperation, AttributeError):
        # Mejorar manejo de errores para casos extremos
        return "0"

@register.filter
def verbose_name(instance, field_name):
    """Obtiene el verbose_name de un campo del modelo"""
    try:
        return instance._meta.get_field(field_name).verbose_name
    except (AttributeError, models.FieldDoesNotExist):
        return field_name.replace('_', ' ').title()

@register.filter
def sub(value, arg):
    """Resta el argumento del valor"""
    try:
        if isinstance(value, str):
            value = Decimal(value)
        if isinstance(arg, str):
            arg = Decimal(arg)
        return value - arg
    except (ValueError, TypeError, InvalidOperation):
        return value

@register.filter
def mul(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        if isinstance(value, str):
            value = Decimal(value)
        if isinstance(arg, str):
            arg = Decimal(arg)
        return value * arg
    except (ValueError, TypeError, InvalidOperation):
        return value

@register.filter
def div(value, arg):
    """Divide el valor por el argumento"""
    try:
        if isinstance(value, str):
            value = Decimal(value)
        if isinstance(arg, str):
            arg = Decimal(arg)
        if arg == 0:
            return value
        return value / arg
    except (ValueError, TypeError, InvalidOperation):
        return value
