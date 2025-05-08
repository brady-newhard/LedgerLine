from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
import calendar
from django.db.models import Sum
import isoweek


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
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='EXPENSE')
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Ensure the date is timezone-aware
        if self.date and not timezone.is_aware(self.date):
            self.date = timezone.make_aware(self.date)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} - {self.description[:30]}"

    @classmethod
    def get_monthly_totals(cls, user, year=None, month=None):
        """
        Get monthly totals for income and expenses for a specific month
        If year and month are not provided, use current month
        """
        from django.db.models import Sum
        from django.utils import timezone
        
        if year is None or month is None:
            now = timezone.now()
            year = now.year
            month = now.month
            
        # Get first and last day of the month
        first_day = timezone.datetime(year, month, 1)
        if month == 12:
            last_day = timezone.datetime(year + 1, 1, 1) - timezone.timedelta(days=1)
        else:
            last_day = timezone.datetime(year, month + 1, 1) - timezone.timedelta(days=1)
            
        # Get transactions for the month
        transactions = cls.objects.filter(
            user=user,
            date__gte=first_day,
            date__lte=last_day
        )
        
        # Calculate totals
        income = transactions.filter(transaction_type='INCOME').aggregate(total=Sum('amount'))['total'] or 0
        expenses = transactions.filter(transaction_type='EXPENSE').aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'income': income,
            'expenses': expenses,
            'net': income - expenses
        }

    @classmethod
    def get_monthly_category_totals(cls, user, year=None, month=None):
        """
        Get monthly totals by category for a specific month
        """
        from django.db.models import Sum
        from django.utils import timezone
        
        if year is None or month is None:
            now = timezone.now()
            year = now.year
            month = now.month
            
        # Get first and last day of the month
        first_day = timezone.datetime(year, month, 1)
        if month == 12:
            last_day = timezone.datetime(year + 1, 1, 1) - timezone.timedelta(days=1)
        else:
            last_day = timezone.datetime(year, month + 1, 1) - timezone.timedelta(days=1)
            
        # Get transactions for the month grouped by category
        transactions = cls.objects.filter(
            user=user,
            date__gte=first_day,
            date__lte=last_day
        ).values('category__category_type', 'transaction_type').annotate(
            total=Sum('amount')
        )
        
        return transactions

    class Meta:
        ordering = ['-date']

class Calendar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()

    class Meta:
        unique_together = ('user', 'year', 'month')

    def __str__(self):
        return f"{self.user.username} - {self.year}-{self.month:02d}"

class Budget(models.Model):
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.calendar.year}-{self.calendar.month:02d})"

    def get_total_spent(self):
        # Sum all amounts of items for this budget
        return self.items.aggregate(total=models.Sum('amount'))['total'] or 0

    def get_remaining(self):
        # Remaining = budgeted amount - total spent
        return self.amount - self.get_total_spent()

class BudgetItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - ${self.amount}"

    class Meta:
        ordering = ['-created_at']

class Income(models.Model):
    INCOME_TYPES = [
        ('SALARY', 'Salary'),
        ('BONUS', 'Bonus'),
        ('SIDE_HUSTLE', 'Side Hustle'),
        ('OTHER', 'Other'),
    ] 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name='incomes')
    income_type = models.CharField(max_length=15, choices=INCOME_TYPES, default='SALARY')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_income_type_display()} - ${self.amount}"

    class Meta:
        ordering = ['-created_at']

class Category(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ("salary", "Salary"),
        ("freelance", "Freelance"),
        ("investments", "Investments"),
        ("bonus", "Bonus"),
        ("utilities", "Utilities"),
        ("gas", "Gas"),
        ("mortgage", "Mortgage"),
        ("rent", "Rent"),
        ("entertainment", "Entertainment"),
        ("transportation", "Transportation"),
        ("dining_out", "Dining Out"),
        ("groceries", "Groceries"),
        ("savings", "Savings"),
        ("other", "Other"),
    ]
    
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default="other")
    custom_name = models.CharField(max_length=100, blank=True, null=True)
    is_income = models.BooleanField(default=False)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    allocation = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

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

class CriticalSpending(models.Model):
    """Model to track critical spending in Lockdown Mode"""
    CATEGORY_CHOICES = [
        ('basic_groceries', 'Basic Groceries'),
        ('essential_meals', 'Essential Meals'),
        ('emergency_food', 'Emergency Food'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_category_display()} - ${self.amount}"
    
    class Meta:
        ordering = ['-date']

class EssentialBill(models.Model):
    """Model to track essential bills in Lockdown Mode"""
    CATEGORY_CHOICES = [
        ('housing', 'Housing (Mortgage/Rent)'),
        ('utilities', 'Utilities'),
        ('transportation', 'Transportation'),
        ('health', 'Healthcare'),
        ('debt', 'Minimum Debt Payments'),
        ('insurance', 'Insurance'),
        ('other', 'Other Essential')
    ]
    
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('scheduled', 'Scheduled'),
        ('deferred', 'Deferred')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    payment_date = models.DateField(null=True, blank=True)
    is_critical = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name} - ${self.amount} - {self.get_status_display()}"
    
    def days_until_due(self):
        """Returns number of days until bill is due"""
        today = timezone.now().date()
        return (self.due_date - today).days
    
    def is_overdue(self):
        """Returns True if bill is overdue and not paid"""
        return self.days_until_due() < 0 and self.status != 'paid'
    
    class Meta:
        ordering = ['due_date']

class SurvivalExpenseSchedule(models.Model):
    """Model to track essential bill schedule for Survival Mode"""
    PRIORITY_CHOICES = [
        ('high', 'High Priority'),
        ('medium', 'Medium Priority'),
        ('low', 'Low Priority'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('scheduled', 'Scheduled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bill_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.bill_name} - ${self.amount} due {self.due_date}"
    
    def is_due_soon(self):
        """Returns True if bill is due within 5 days"""
        if self.status != 'paid':
            today = timezone.now().date()
            days_until_due = (self.due_date - today).days
            return days_until_due <= 5 and days_until_due >= 0
        return False
    
    def is_overdue(self):
        """Returns True if bill is overdue"""
        if self.status != 'paid':
            today = timezone.now().date()
            return self.due_date < today
        return False
    
    class Meta:
        ordering = ['due_date']

class StabilityRatioTarget(models.Model):
    """Model to track income/expense ratio targets for Stability Mode"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    income_target = models.DecimalField(max_digits=10, decimal_places=2)
    expense_target = models.DecimalField(max_digits=10, decimal_places=2)
    ratio_target = models.DecimalField(max_digits=5, decimal_places=4)
    month = models.DateField()  # First day of the month this target is for
    is_achieved = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - Target ratio: {self.ratio_target} for {self.month.strftime('%B %Y')}"
    
    class Meta:
        ordering = ['-month']
        unique_together = ['user', 'month']

class CategorySpendingLimit(models.Model):
    """Model to track category spending limits for Stability Mode"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    limit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()  # First day of the month this limit is for
    warning_threshold = models.IntegerField(default=80)  # Percentage of limit when warning triggers
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.category} limit: ${self.limit_amount}"
    
    class Meta:
        ordering = ['-month']
        unique_together = ['user', 'category', 'month']

class SavingsGoal(models.Model):
    """Model to track savings goals for Saver Mode"""
    GOAL_TYPE_CHOICES = [
        ('emergency', 'Emergency Fund'),
        ('retirement', 'Retirement'),
        ('house', 'House Down Payment'),
        ('car', 'Vehicle'),
        ('vacation', 'Vacation'),
        ('education', 'Education'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES, default='other')
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(default=timezone.now)
    target_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    icon = models.CharField(max_length=20, default='💰')
    priority = models.IntegerField(default=1)  # 1 is highest priority
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name} - ${self.current_amount}/{self.target_amount}"
    
    def progress_percentage(self):
        """Returns percentage progress toward goal"""
        if self.target_amount == 0:
            return 100
        return min(100, int((self.current_amount / self.target_amount) * 100))
    
    def monthly_target(self):
        """Returns monthly savings needed to reach goal on time"""
        if not self.target_date:
            return 0
        
        today = timezone.now().date()
        if today >= self.target_date:
            return self.target_amount - self.current_amount
            
        months_remaining = (self.target_date.year - today.year) * 12 + self.target_date.month - today.month
        if months_remaining <= 0:
            return self.target_amount - self.current_amount
            
        return (self.target_amount - self.current_amount) / months_remaining
    
    class Meta:
        ordering = ['priority', 'target_date']

class SavingsContribution(models.Model):
    """Model to track contributions to savings goals"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        goal_name = self.goal.name if self.goal else "General Savings"
        return f"{self.user.username} - ${self.amount} to {goal_name} on {self.date}"
    
    class Meta:
        ordering = ['-date']

class FreedomFundPlan(models.Model):
    """Model to track freedom fund planning for Vacay Mode"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.DateField()  # First day of the month this plan is for
    discretionary_amount = models.DecimalField(max_digits=10, decimal_places=2)
    freedom_allocation = models.DecimalField(max_digits=10, decimal_places=2)
    savings_allocation = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - Freedom Fund: ${self.freedom_allocation} for {self.month.strftime('%B %Y')}"
    
    class Meta:
        ordering = ['-month']
        unique_together = ['user', 'month']

class FreedomExpense(models.Model):
    """Model to track freedom fund expenses in Vacay Mode"""
    CATEGORY_CHOICES = [
        ('travel', 'Travel'),
        ('entertainment', 'Entertainment'),
        ('dining', 'Fine Dining'),
        ('shopping', 'Luxury Shopping'),
        ('experience', 'Experiences'),
        ('gift', 'Gifts'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(FreedomFundPlan, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=200)
    location = models.CharField(max_length=100, blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount} for {self.get_category_display()}: {self.description}"
    
    class Meta:
        ordering = ['-date']
