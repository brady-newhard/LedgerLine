from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

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
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='EXPENSE')
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} - {self.description[:30]}"

    class Meta:
        ordering = ['-date']

class Category(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ("utilities", "Utilities"),
        ("gas", "Gas"),
        ("mortgage", "Mortgage"),
        ("rent", "Rent"),
        ("entertainment", "Entertainment"),
        ("transportation", "Transportation"),
        ("dining_out", "Dining Out"),
        ("groceries", "Groceries"),
        ("other", "Other"),
    ]
    ICON_CHOICES = [
        ("fa-bolt", "Utilities ⚡"),
        ("fa-gas-pump", "Gas ⛽"),
        ("fa-home", "Mortgage 🏠"),
        ("fa-building", "Rent 🏢"),
        ("fa-film", "Entertainment 🎬"),
        ("fa-bus", "Transportation 🚌"),
        ("fa-utensils", "Dining Out 🍽️"),
        ("fa-shopping-cart", "Groceries 🛒"),
        ("fa-question", "Other ❓"),
    ]
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default="other")
    custom_name = models.CharField(max_length=100, blank=True, null=True)
    icon = models.CharField(max_length=32, choices=ICON_CHOICES, default="fa-question")
    is_income = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default="#00ff00")
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.custom_name if self.custom_name else self.get_category_type_display()}"

    def get_remaining_budget(self):
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import datetime

        # Get the first day of the current month
        today = timezone.now()
        first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate total transactions for this category in the current month
        total_transactions = self.transaction_set.filter(
            date__gte=first_day,
            date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        # For income categories, remaining budget is budget minus total transactions
        # For expense categories, remaining budget is budget plus total transactions
        if self.is_income:
            return self.budget - total_transactions
        else:
            return self.budget + total_transactions

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['category_type']
