from django.utils import timezone
from .models import ModeUnlock, Transaction
from django.contrib import messages

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
