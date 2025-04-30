from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def divided_by(value, arg):
    """Divides the value by the argument"""
    try:
        if value is None:
            return 0
        if arg is None or arg == 0:
            return 0
        return value / arg
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        if value is None:
            return 0
        return value * arg
    except ValueError:
        return 0 