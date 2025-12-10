from django import template
from decimal import Decimal, InvalidOperation # Import Decimal and InvalidOperation

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return Decimal(value) * Decimal(arg)
    except (InvalidOperation, TypeError):
        return Decimal(0)

@register.filter
def subtract(value, arg):
    try:
        return Decimal(value) - Decimal(arg)
    except (InvalidOperation, TypeError):
        return Decimal(0)

@register.filter
def divide(value, arg):
    try:
        # Ensure arg is not zero to prevent ZeroDivisionError
        decimal_arg = Decimal(arg)
        if decimal_arg == Decimal(0):
            return Decimal(0)
        return Decimal(value) / decimal_arg
    except (InvalidOperation, TypeError, ZeroDivisionError): # Catch ZeroDivisionError for safety
        return Decimal(0)

@register.filter
def as_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
