from django.utils import timezone
from datetime import datetime
import calendar
from .models import ModeUnlock, Transaction
from django.contrib import messages
import re
from django.core.exceptions import ValidationError
import isoweek

def check_and_unlock_modes(user):
    transactions = Transaction.objects.filter(user=user)
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'EXPENSE')
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'INCOME')

    # Example: Unlock Lockdown Mode if expenses > income
    if total_expenses > total_income:
        mode, created = ModeUnlock.objects.get_or_create(
            user=user,
            name="Lockdown Mode",
            defaults={
                "description": "Triggered when expenses exceed income.",
                "is_unlocked": True,
                "triggered_on": timezone.now()
            }
        )
        if not mode.is_unlocked:
            mode.is_unlocked = True
            mode.triggered_on = timezone.now()
            mode.save()

# ANSI Shadow Text Templates
# Each letter is represented as a list of strings, with each string being a line
ANSI_SHADOW_LETTERS = {
    'A': [
        '██╗  ',
        '██║  ',
        '███████╗',
        '██╔══██║',
        '██║  ██║',
        '╚═╝  ╚═╝'
    ],
    'B': [
        '██████╗ ',
        '██╔══██╗',
        '██████╔╝',
        '██╔══██╗',
        '██████╔╝',
        '╚═════╝ '
    ],
    'C': [
        ' ██████╗',
        '██╔════╝',
        '██║     ',
        '██║     ',
        '╚██████╗',
        ' ╚═════╝'
    ],
    'D': [
        '██████╗ ',
        '██╔══██╗',
        '██║  ██║',
        '██║  ██║',
        '██████╔╝',
        '╚═════╝ '
    ],
    'E': [
        '███████╗',
        '██╔════╝',
        '█████╗  ',
        '██╔══╝  ',
        '███████╗',
        '╚══════╝'
    ],
    'F': [
        '███████╗',
        '██╔════╝',
        '█████╗  ',
        '██╔══╝  ',
        '██║     ',
        '╚═╝     '
    ],
    'G': [
        ' ██████╗ ',
        '██╔════╝ ',
        '██║  ███╗',
        '██║   ██║',
        '╚██████╔╝',
        ' ╚═════╝ '
    ],
    'H': [
        '██╗  ██╗',
        '██║  ██║',
        '███████║',
        '██╔══██║',
        '██║  ██║',
        '╚═╝  ╚═╝'
    ],
    'I': [
        '██╗',
        '██║',
        '██║',
        '██║',
        '██║',
        '╚═╝'
    ],
    'J': [
        '     ██╗',
        '     ██║',
        '     ██║',
        '██   ██║',
        '╚█████╔╝',
        ' ╚════╝ '
    ],
    'K': [
        '██╗  ██╗',
        '██║ ██╔╝',
        '█████╔╝ ',
        '██╔═██╗ ',
        '██║  ██╗',
        '╚═╝  ╚═╝'
    ],
    'L': [
        '██╗     ',
        '██║     ',
        '██║     ',
        '██║     ',
        '███████╗',
        '╚══════╝'
    ],
    'M': [
        '███╗   ███╗',
        '████╗ ████║',
        '██╔████╔██║',
        '██║╚██╔╝██║',
        '██║ ╚═╝ ██║',
        '╚═╝     ╚═╝'
    ],
    'N': [
        '███╗   ██╗',
        '████╗  ██║',
        '██╔██╗ ██║',
        '██║╚██╗██║',
        '██║ ╚████║',
        '╚═╝  ╚═══╝'
    ],
    'O': [
        ' ██████╗ ',
        '██╔═══██╗',
        '██║   ██║',
        '██║   ██║',
        '╚██████╔╝',
        ' ╚═════╝ '
    ],
    'P': [
        '██████╗ ',
        '██╔══██╗',
        '██████╔╝',
        '██╔═══╝ ',
        '██║     ',
        '╚═╝     '
    ],
    'Q': [
        ' ██████╗ ',
        '██╔═══██╗',
        '██║   ██║',
        '██║▄▄ ██║',
        '╚██████╔╝',
        ' ╚══▀▀═╝ '
    ],
    'R': [
        '██████╗ ',
        '██╔══██╗',
        '██████╔╝',
        '██╔══██╗',
        '██║  ██║',
        '╚═╝  ╚═╝'
    ],
    'S': [
        '███████╗',
        '██╔════╝',
        '███████╗',
        '╚════██║',
        '███████║',
        '╚══════╝'
    ],
    'T': [
        '████████╗',
        '╚══██╔══╝',
        '   ██║   ',
        '   ██║   ',
        '   ██║   ',
        '   ╚═╝   '
    ],
    'U': [
        '██╗   ██╗',
        '██║   ██║',
        '██║   ██║',
        '██║   ██║',
        '╚██████╔╝',
        ' ╚═════╝ '
    ],
    'V': [
        '██╗   ██╗',
        '██║   ██║',
        '██║   ██║',
        '╚██╗ ██╔╝',
        ' ╚████╔╝ ',
        '  ╚═══╝  '
    ],
    'W': [
        '██╗    ██╗',
        '██║    ██║',
        '██║ █╗ ██║',
        '██║███╗██║',
        '╚███╔███╔╝',
        ' ╚══╝╚══╝ '
    ],
    'X': [
        '██╗  ██╗',
        '╚██╗██╔╝',
        ' ╚███╔╝ ',
        ' ██╔██╗ ',
        '██╔╝ ██╗',
        '╚═╝  ╚═╝'
    ],
    'Y': [
        '██╗   ██╗',
        '╚██╗ ██╔╝',
        ' ╚████╔╝ ',
        '  ╚██╔╝  ',
        '   ██║   ',
        '   ╚═╝   '
    ],
    'Z': [
        '███████╗',
        '╚══███╔╝',
        '  ███╔╝ ',
        ' ███╔╝  ',
        '███████╗',
        '╚══════╝'
    ],
    ' ': [
        '  ',
        '  ',
        '  ',
        '  ',
        '  ',
        '  '
    ]
}

def generate_ansi_shadow_title(text):
    """Generate ANSI shadow text for titles"""
    text = text.upper()  # Convert to uppercase
    
    # Initialize lines
    lines = ['', '', '', '', '', '']
    
    # Add each character
    for char in text:
        if char in ANSI_SHADOW_LETTERS:
            for i, line in enumerate(ANSI_SHADOW_LETTERS[char]):
                lines[i] += line
        else:
            # For characters not in our dictionary, use space
            for i in range(6):
                lines[i] += '  '
    
    # Join lines with newlines and return
    return '\n'.join(lines)

def get_month_year_choices():
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    choices = []
    
    for year in range(current_year - 5, current_year + 6):
        for month in range(1, 13):
            if year == current_year and month > current_month:
                continue
            month_name = calendar.month_name[month]
            display = f"{month_name} {year}"
            value = f"{year}-{month:02d}"
            choices.append((value, display))
    return choices
def get_year_choices():
    now = datetime.now()
    return [(str(y), str(y)) for y in range(now.year - 5, now.year + 6)]

def get_week_choices():
    now = datetime.now()
    choices = []
    for year in range(now.year - 5, now.year + 6):
        for week in range(1, 53):
            w = isoweek.Week(year, week)
            display = f"Week of {w.monday()} – {w.sunday()}"
            value = f"{year}-W{week:02d}"
            choices.append((value, display))
    return choices
def validate_date_based_on_type(date_value, budgeting_type):
    if budgeting_type == 'ANNUALLY' and not re.match(r'^\d{4}$', date_value.strip()):
        raise ValidationError("For annually, enter a valid year like 2025.")
    elif budgeting_type == 'MONTHLY' and not re.match(r'^\d{4}-\d{2}$', date_value.strip()):
        raise ValidationError("Enter a valid month-year like 2025-04.")
    elif budgeting_type == 'WEEKLY' and not re.match(r'^\d{4}-W\d{2}$', date_value.strip()):
        raise ValidationError("Enter a valid ISO week like 2025-W14.")  