import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LedgerLine.settings')
django.setup()

from main_app.models import ModeUnlock, User, CriticalSpending
from django.utils import timezone
from decimal import Decimal

# Update lockdown mode for all users
for user in User.objects.all():
    mode = ModeUnlock.objects.filter(user=user, name='Lockdown Mode').first()
    if mode:
        print(f"Updating Lockdown Mode for {user.username}")
        mode.is_unlocked = True
        mode.triggered_on = timezone.now()
        mode.save()
        
        # Create a sample critical spending entry
        try:
            critical_spending = CriticalSpending.objects.create(
                user=user,
                category='basic_groceries',
                amount=Decimal('25.00'),
                notes='Test entry for basic groceries'
            )
            print(f"Created critical spending entry for {user.username}")
        except Exception as e:
            print(f"Error creating critical spending: {e}")
    else:
        print(f"No Lockdown Mode found for {user.username}") 