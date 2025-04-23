from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ModeUnlock(models.Model):
    """
    Model to track which modes each user has unlocked.
    
    Icon examples include:
    - 💰 Money bag for general finance
    - 📈 Chart for investment/growth
    - 📉 Downward chart for expense reduction
    - 💸 Flying money for spending
    - 🔄 Recycling for recurring payments
    - 🎯 Target for goals
    - 🏦 Bank for savings
    - 💳 Credit card for credit tracking
    - 📊 Bar chart for analytics
    - 🛒 Shopping cart for purchases
    - 📆 Calendar for scheduled payments
    - 🔔 Bell for reminders
    - 🔐 Lock for security features
    - ⚡ Lightning for quick transactions
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10, default="💰")
    is_unlocked = models.BooleanField(default=False)
    triggered_on = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=0)  # Track consecutive days in this mode

    def __str__(self):
        unlock_status = "Unlocked" if self.is_unlocked else "Locked"
        return f"{self.name} - {unlock_status} for {self.user.username}"

class ModeHistory(models.Model):
    """Model to track history of mode changes and progress"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mode_name = models.CharField(max_length=50)
    status_change = models.CharField(max_length=50, choices=[
        ('unlocked', 'Mode Unlocked'),
        ('locked', 'Mode Locked'),
        ('progress', 'Progress Updated')
    ])
    progress_percentage = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.mode_name} - {self.status_change} on {self.timestamp.strftime('%Y-%m-%d')}"

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
