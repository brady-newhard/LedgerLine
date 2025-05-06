from django import forms
from .utils import get_month_year_choices  
from .utils import validate_date_based_on_type
from .models import Budget, BudgetItem, Income, Calendar
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Category, Transaction
from django.utils import timezone
from datetime import datetime
import re
from django.core.exceptions import ValidationError

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
    

class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ['year', 'month']

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount']

class BudgetItemForm(forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ['name', 'amount']

INCOME_TYPES = [
    ('SALARY', 'Salary'),
    ('BONUS', 'Bonus'),
    ('SIDE_HUSTLE', 'Side Hustle'),
    ('OTHER', 'Other'),
]

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['income_type', 'amount']
        widgets = {
            'income_type': forms.Select(choices=INCOME_TYPES, attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': '0'}),
        }
   
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_type', 'custom_name', 'is_income', 'allocation']
        widgets = {
            'allocation': forms.NumberInput(attrs={'placeholder': 'Enter allocation amount', 'step': '0.01'}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'description', 'category', 'date']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        # Set initial date to current time in local timezone
        self.initial['date'] = timezone.localtime(timezone.now()) 
        self.fields['category'].queryset = Category.objects.filter(user=user) 


