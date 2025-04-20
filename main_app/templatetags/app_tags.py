from django import template
from main_app.utils import generate_ansi_shadow_title

register = template.Library()

@register.simple_tag
def ansi_shadow(text):
    """
    Creates ANSI shadow text for templates
    Usage: {% ansi_shadow "YOUR TEXT" %}
    """
    return generate_ansi_shadow_title(text)

@register.simple_tag
def ansi_shadow_test(text):
    """Simple test tag"""
    return f"ANSI SHADOW: {text}" 