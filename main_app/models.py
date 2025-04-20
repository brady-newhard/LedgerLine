from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ModeUnlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_unlocked = models.BooleanField(default=False)
    triggered_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {'Unlocked' if self.is_unlocked else 'Locked'}"

# NOTE: Transaction Model commented out on [date]
# This was implemented as part of UI exploration but is actually
# not assigned to me. Commenting out to avoid conflict
# with their implementation. It allowed some functionality to seem

# class Transaction(models.Model):
#     ...


# class Transaction(models.Model):
#     TRANSACTION_TYPES = [
#         ('INCOME', 'Income'),
#         ('EXPENSE', 'Expense'),
#     ]
    
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     description = models.CharField(max_length=255)
#     transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
#     date = models.DateField(default=timezone.now)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"{self.transaction_type}: ${self.amount} - {self.description}"
