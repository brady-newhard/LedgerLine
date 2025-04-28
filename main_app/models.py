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

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('EXPENSE', 'Expense'),
        ('INCOME', 'Income'),     
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    # category = models.CharField(max_length=20, choices=CATEGORIES, default='OTHER')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='EXPENSE')
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} - {self.description[:30]}"

    class Meta:
        ordering = ['-date']

class Budget(models.Model):
    BUDGETING_TYPES = [
        ('MONTHLY', 'Monthly'),
        ('ANNUALLY', 'Annually'),
        ('WEEKLY', 'Weekly'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    budget_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    budgeting_type = models.CharField(max_length=10, choices=BUDGETING_TYPES, default='MONTHLY')
    # category = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"{self.get_budgeting_type_display()} Budget: ${self.amount}"
    
    def get_total_spent(self):
        return sum(item.amount for item in self.budgetitem_set.all())
    
    def get_remaining(self):
        return self.amount - self.get_total_spent()

class BudgetItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ${self.amount}"
    
    class Meta:
        ordering = ['-created_at']
        
