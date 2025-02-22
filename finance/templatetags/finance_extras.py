from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """Retorna el valor absoluto de un número"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """Resta dos números"""
    try:
        return value - arg
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide dos números"""
    try:
        if arg == 0:
            return 0
        return value / arg
    except (ValueError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplica dos números"""
    try:
        return value * arg
    except (ValueError, TypeError):
        return 0

@register.filter
def month_name_es(month_number):
    """Retorna el nombre del mes en español"""
    meses = {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Septiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre'
    }
    return meses.get(month_number, '')
