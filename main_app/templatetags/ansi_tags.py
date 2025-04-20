from django import template

register = template.Library()

@register.filter
def ansi(text):
    return f"ANSI: {text}"