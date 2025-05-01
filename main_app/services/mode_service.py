from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
import math
import calendar

class ModeService:
    """
    Service class responsible for checking and managing mode unlock conditions.
    Each mode has its own method to check unlock conditions.
    """
    
    @staticmethod
    def check_lockdown_mode(user, transactions=None):
        """
        Lockdown Mode: Triggered when expenses exceed income
        """
        from main_app.models import Transaction  # Import here to avoid circular imports
        
        if not transactions:
            transactions = Transaction.objects.filter(user=user)
            
        total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'EXPENSE')
        total_income = sum(t.amount for t in transactions if t.transaction_type == 'INCOME')
        
        # Calculate progress percentage
        if total_income > 0:
            expense_ratio = total_expenses / total_income
            if expense_ratio >= 1:
                progress = 100  # Already unlocked
            else:
                # Scale from 0-100% as expense ratio goes from 0 to 1
                progress = min(100, math.floor(expense_ratio * 100))
        else:
            progress = 0
            
        return {
            'is_unlocked': total_expenses > total_income,
            'name': 'Lockdown Mode',
            'description': 'Triggered when expenses exceed income. Time to evaluate spending and cut back on non-essentials.',
            'icon': '🔒',
            'progress': progress,
            'notes': f"Total expenses: ${total_expenses}, Total income: ${total_income}"
        }
    
    @staticmethod
    def check_vacay_mode(user, transactions=None):
        """
        Vacay Mode: Triggered by sustained savings (3+ months where income > expenses by at least 15%)
        """
        from main_app.models import Transaction  # Import here to avoid circular imports
        
        if not transactions:
            transactions = Transaction.objects.filter(user=user)
        
        # Check the last 3 months
        three_months_ago = timezone.now() - timedelta(days=90)
        recent_transactions = transactions.filter(date__isnull=False, date__gte=three_months_ago)
        
        # Group by month and check if each month has savings
        months = {}
        for t in recent_transactions:
            # Skip transactions with None date - belt and suspenders approach
            if t.date is None:
                continue
            
            month_key = (t.date.year, t.date.month)
            if month_key not in months:
                months[month_key] = {'income': Decimal('0'), 'expenses': Decimal('0')}
            
            if t.transaction_type == 'INCOME':
                months[month_key]['income'] += t.amount
            else:
                months[month_key]['expenses'] += t.amount
        
        # Check if we have at least 3 months of data with savings >= 15%
        savings_months = 0
        total_months = len(months)
        notes = []
        
        for month_key, month_data in months.items():
            if month_data['income'] > 0 and month_data['expenses'] >= 0:
                savings_rate = (month_data['income'] - month_data['expenses']) / month_data['income']
                month_name = f"{month_key[0]}-{month_key[1]}"
                savings_pct = round(savings_rate * 100, 1)
                notes.append(f"{month_name}: {savings_pct}% savings rate")
                
                if savings_rate >= Decimal('0.15'):  # 15% savings rate
                    savings_months += 1
        
        # Calculate progress - need 3 months with 15% savings
        if total_months > 0:
            progress = min(100, math.floor((savings_months / 3) * 100))
        else:
            progress = 0
            
        notes_text = " | ".join(notes) if notes else "No monthly data available yet"
        
        return {
            'is_unlocked': savings_months >= 3,
            'name': 'Vacay Mode',
            'description': 'Triggered by sustained savings over 3+ months. You\'re building financial freedom!',
            'icon': '🏝️',
            'progress': progress,
            'notes': f"Months with 15%+ savings: {savings_months}/3 needed. {notes_text}"
        }
    
    @staticmethod
    def check_survival_mode(user, transactions=None):
        """
        Survival Mode: Triggered by intense early-month spending (>50% of monthly income spent in first 10 days)
        """
        from main_app.models import Transaction  # Import here to avoid circular imports
        
        if not transactions:
            transactions = Transaction.objects.filter(user=user)
        
        # Get current month transactions
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        progress = 0
        is_survival_mode = False
        notes = "Not in first 10 days of the month"
        
        # Check if we're past the 10th day of the month
        if now.day <= 10:
            # Get last month's income as reference
            previous_month = (start_of_month - timedelta(days=1)).replace(day=1)
            
            # Filter out transactions with None dates
            previous_month_income = transactions.filter(
                transaction_type='INCOME', 
                date__isnull=False,
                date__gte=previous_month,
                date__lt=start_of_month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Early month expenses - filter out None dates
            early_month_expenses = transactions.filter(
                transaction_type='EXPENSE',
                date__isnull=False,
                date__gte=start_of_month,
                date__lte=now
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Calculate progress
            if previous_month_income > 0:
                expense_ratio = early_month_expenses / previous_month_income
                progress = min(100, math.floor(expense_ratio * 100))
                is_survival_mode = expense_ratio > Decimal('0.5')
                notes = f"Early month spending: ${early_month_expenses} of ${previous_month_income} ({progress}%)"
            else:
                notes = "No income data from previous month"
        
        return {
            'is_unlocked': is_survival_mode,
            'name': 'Survival Mode',
            'description': 'Triggered by spending >50% of monthly income in the first 10 days. Budget carefully!',
            'icon': '⚠️',
            'progress': progress,
            'notes': notes
        }
    
    @staticmethod
    def check_stability_mode(user, transactions=None):
        """
        Stability Mode: Triggered by consistent income/expense ratio (within 10% fluctuation for 4+ months)
        """
        from main_app.models import Transaction  # Import here to avoid circular imports
        
        if not transactions:
            transactions = Transaction.objects.filter(user=user)
        
        # Check the last 4 months
        four_months_ago = timezone.now() - timedelta(days=120)
        recent_transactions = transactions.filter(date__isnull=False, date__gte=four_months_ago)
        
        # Group by month and calculate income/expense ratio
        months = {}
        for t in recent_transactions:
            # Skip transactions with None date
            if t.date is None:
                continue
            
            month_key = (t.date.year, t.date.month)
            if month_key not in months:
                months[month_key] = {'income': Decimal('0'), 'expenses': Decimal('0')}
            
            if t.transaction_type == 'INCOME':
                months[month_key]['income'] += t.amount
            else:
                months[month_key]['expenses'] += t.amount
        
        # Calculate ratios for each month
        ratios = []
        month_details = []
        
        for month_key, month_data in months.items():
            if month_data['income'] > 0 and month_data['expenses'] > 0:
                ratio = month_data['expenses'] / month_data['income']
                ratios.append(ratio)
                month_details.append(f"{month_key[0]}-{month_key[1]}: {round(ratio * 100)}%")
        
        # Calculate progress - need 4 months of consistent ratios
        stability_achieved = False
        progress = 0
        notes = "Insufficient monthly data"
        
        if len(ratios) >= 4:
            # Check if all ratios are within 10% of the average
            avg_ratio = sum(ratios) / len(ratios)
            consistent_months = 0
            
            for ratio in ratios:
                if abs(ratio - avg_ratio) / avg_ratio <= Decimal('0.1'):
                    consistent_months += 1
            
            stability_achieved = consistent_months >= 4
            progress = min(100, math.floor((consistent_months / 4) * 100))
            notes = f"Consistent months: {consistent_months}/4 needed. Average ratio: {round(avg_ratio * 100)}%. {' | '.join(month_details)}"
        else:
            # Still tracking progress even with fewer months
            progress = min(75, math.floor((len(ratios) / 4) * 100))
            notes = f"Months with data: {len(ratios)}/4 needed. {' | '.join(month_details)}"
        
        return {
            'is_unlocked': stability_achieved,
            'name': 'Stability Mode',
            'description': 'Triggered by consistent income/expense ratio over 4+ months. Financial stability achieved!',
            'icon': '🏆',
            'progress': progress,
            'notes': notes
        }
    
    @staticmethod
    def check_saver_mode(user, transactions=None):
        """
        Saver Mode: Triggered when total savings exceed 3x monthly income
        """
        from main_app.models import Transaction  # Import here to avoid circular imports
        
        if not transactions:
            transactions = Transaction.objects.filter(user=user)
        
        # Calculate total savings (all-time income minus all-time expenses)
        total_income = sum(t.amount for t in transactions if t.transaction_type == 'INCOME')
        total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'EXPENSE')
        total_savings = total_income - total_expenses
        
        # Calculate average monthly income over the last 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        recent_income = transactions.filter(
            transaction_type='INCOME',
            date__isnull=False,
            date__gte=six_months_ago
        )
        
        # Group by month to calculate average monthly income
        months = {}
        for t in recent_income:
            # Skip transactions with None date
            if t.date is None:
                continue
            
            month_key = (t.date.year, t.date.month)
            if month_key not in months:
                months[month_key] = Decimal('0')
            months[month_key] += t.amount
        
        progress = 0
        is_saver = False
        notes = "Insufficient income data"
        
        if months:
            avg_monthly_income = sum(months.values()) / len(months)
            target = avg_monthly_income * 3
            
            if target > 0:
                progress = min(100, math.floor((total_savings / target) * 100))
                is_saver = total_savings >= target
                notes = f"Savings: ${total_savings} of ${target} target (3x monthly income of ${avg_monthly_income})"
        
        return {
            'is_unlocked': is_saver,
            'name': 'Saver Mode',
            'description': 'Triggered when total savings exceed 3x monthly income. You\'re building financial security!',
            'icon': '💰',
            'progress': progress,
            'notes': notes
        }
    
    @classmethod
    def check_all_modes(cls, user):
        """
        Check all financial modes for a user and return combined results
        """
        modes = {
            'lockdown_mode': cls.check_lockdown_mode(user),
            'vacay_mode': cls.check_vacay_mode(user),
            'survival_mode': cls.check_survival_mode(user),
            'stability_mode': cls.check_stability_mode(user),
            'saver_mode': cls.check_saver_mode(user),
        }
        return modes
    
    @classmethod
    def update_user_modes(cls, user):
        """
        Check all mode conditions and update the database
        Returns a list of newly unlocked modes
        """
        from main_app.models import ModeUnlock, ModeHistory  # Import here to avoid circular imports
        
        # Check all mode conditions
        mode_results = cls.check_all_modes(user)
        newly_unlocked = []
        
        # Update database for each mode
        for mode_data in mode_results.values():
            mode, created = ModeUnlock.objects.get_or_create(
                user=user,
                name=mode_data['name'],
                defaults={
                    "description": mode_data['description'],
                    "is_unlocked": mode_data['is_unlocked'],
                    "triggered_on": timezone.now() if mode_data['is_unlocked'] else None,
                    "icon": mode_data.get('icon', ''),
                    "progress_percentage": mode_data.get('progress', 0)
                }
            )
            
            # Update progress percentage
            if not created and mode.progress_percentage != mode_data.get('progress', 0):
                # Log progress update to history
                ModeHistory.objects.create(
                    user=user,
                    mode_name=mode_data['name'],
                    status_change='progress',
                    progress_percentage=mode_data.get('progress', 0),
                    details=mode_data.get('notes', '')
                )
                
                mode.progress_percentage = mode_data.get('progress', 0)
                mode.save(update_fields=['progress_percentage'])
            
            # If mode exists but unlock status has changed
            if not created and mode.is_unlocked != mode_data['is_unlocked']:
                # Log the status change to history
                ModeHistory.objects.create(
                    user=user,
                    mode_name=mode_data['name'],
                    status_change='unlocked' if mode_data['is_unlocked'] else 'locked',
                    progress_percentage=mode_data.get('progress', 0),
                    details=mode_data.get('notes', '')
                )
                
                # Update the mode status
                mode.is_unlocked = mode_data['is_unlocked']
                if mode_data['is_unlocked']:
                    mode.triggered_on = timezone.now()
                    newly_unlocked.append(mode)
                
                mode.save()
                
            # If new mode was created and it's unlocked
            elif created and mode_data['is_unlocked']:
                # Also log the initial unlock to history
                ModeHistory.objects.create(
                    user=user,
                    mode_name=mode_data['name'],
                    status_change='unlocked',
                    progress_percentage=mode_data.get('progress', 0),
                    details=mode_data.get('notes', '')
                )
                
                newly_unlocked.append(mode)
                
        return newly_unlocked
    
    @classmethod
    def get_user_mode_history(cls, user):
        """
        Retrieve the user's mode history for the journey map
        """
        from main_app.models import ModeHistory
        
        # Get all mode history events ordered by timestamp (newest first)
        history_events = ModeHistory.objects.filter(user=user).order_by('-timestamp')
        
        # Group history events by mode
        mode_history = {}
        for event in history_events:
            if event.mode_name not in mode_history:
                mode_history[event.mode_name] = []
            mode_history[event.mode_name].append(event)
        
        return mode_history
    
    @classmethod
    def get_mode_dashboard_data(cls, user, mode_name):
        """
        Get detailed data for a specific mode's dashboard
        """
        from main_app.models import ModeUnlock, Transaction, CriticalSpending, EssentialBill
        from django.db.models import Sum
        from datetime import datetime, timedelta
        from decimal import Decimal
        
        # Helper function to convert Decimal to float recursively
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(i) for i in obj]
            else:
                return obj
        
        # Get the mode data
        mode = ModeUnlock.objects.filter(user=user, name=mode_name).first()
        if not mode:
            return None
        
        # Get current financial data
        transactions = Transaction.objects.filter(user=user)
        total_income = sum(t.amount for t in transactions if t.transaction_type == 'INCOME')
        total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'EXPENSE')
        savings = total_income - total_expenses
        
        # Get mode-specific data
        mode_data = {}
        
        if mode_name == "Lockdown Mode":
            mode_data = cls.check_lockdown_mode(user, transactions)
            
            # Get today's date and calculate days left in month
            today = timezone.now().date()
            last_day_of_month = calendar.monthrange(today.year, today.month)[1]
            last_date_of_month = today.replace(day=last_day_of_month)
            days_left_in_month = (last_date_of_month - today).days + 1
            
            # Calculate basic food budget based on 15% of income (or minimum amount if no income)
            base_amount = total_income * Decimal('0.15') if total_income > 0 else Decimal('100')
            
            # Get month start date
            first_day = today.replace(day=1)
            
            # Get all critical spending categories
            critical_categories = {
                'food': {
                    'basic_groceries': {
                        'amount': round(base_amount * Decimal('0.6'), 2),
                        'spent': Decimal('0'),
                        'icon': '🛒',
                        'description': 'Essential groceries like bread, milk, eggs, rice, beans',
                        'priority': 1
                    },
                    'essential_meals': {
                        'amount': round(base_amount * Decimal('0.3'), 2),
                        'spent': Decimal('0'),
                        'icon': '🍚',
                        'description': 'Basic meal essentials and staples',
                        'priority': 1
                    },
                    'emergency_food': {
                        'amount': round(base_amount * Decimal('0.1'), 2),
                        'spent': Decimal('0'),
                        'icon': '🥫',
                        'description': 'Emergency food reserves',
                        'priority': 1
                    }
                },
                'transportation': {
                    'amount': round(base_amount * Decimal('0.5'), 2),
                    'spent': Decimal('0'),
                    'icon': '🚌',
                    'description': 'Essential transportation costs',
                    'priority': 2
                },
                'health': {
                    'amount': round(base_amount * Decimal('0.35'), 2),
                    'spent': Decimal('0'),
                    'icon': '💊',
                    'description': 'Healthcare needs and medicine',
                    'priority': 2
                }
            }
            
            # Get spending for food categories
            basic_groceries_spent = CriticalSpending.objects.filter(
                user=user,
                category='basic_groceries',
                date__gte=first_day
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            essential_meals_spent = CriticalSpending.objects.filter(
                user=user,
                category='essential_meals',
                date__gte=first_day
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            emergency_food_spent = CriticalSpending.objects.filter(
                user=user,
                category='emergency_food',
                date__gte=first_day
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Update spent values
            critical_categories['food']['basic_groceries']['spent'] = basic_groceries_spent
            critical_categories['food']['essential_meals']['spent'] = essential_meals_spent
            critical_categories['food']['emergency_food']['spent'] = emergency_food_spent
            
            # Calculate other categories spending from transactions
            transportation_spent = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                category__category_type='transportation',
                date__gte=first_day
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            health_spent = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                category__category_type__in=['healthcare', 'health'],
                date__gte=first_day
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            critical_categories['transportation']['spent'] = transportation_spent
            critical_categories['health']['spent'] = health_spent
            
            # Calculate totals first
            food_total_amount = sum(cat['amount'] for cat in critical_categories['food'].values())
            food_total_spent = sum(cat['spent'] for cat in critical_categories['food'].values())
            
            # Prepare data for template
            mode_data['critical_spending'] = critical_categories['food']
            mode_data['critical_spending']['total_amount'] = food_total_amount
            mode_data['critical_spending']['total_spent'] = food_total_spent
            
            mode_data['critical_categories'] = {
                'transportation': critical_categories['transportation'],
                'health': critical_categories['health']
            }
            
            mode_data['days_left_in_month'] = days_left_in_month
            mode_data['total_critical_budget'] = food_total_amount
            mode_data['total_critical_spent'] = food_total_spent
            mode_data['money_left_to_spend'] = food_total_amount - food_total_spent
            mode_data['daily_allowance'] = (food_total_amount - food_total_spent) / days_left_in_month if days_left_in_month > 0 else Decimal('0')
            
            # Get essential bills status
            essential_bills = EssentialBill.objects.filter(user=user)
            
            # If no essential bills exist yet, create some default ones
            if not essential_bills.exists():
                # This can be moved to a separate method for initializing bills
                pass
            
            # Get bills by category
            bills_by_category = {}
            for category in EssentialBill.CATEGORY_CHOICES:
                cat_code = category[0]
                bills = essential_bills.filter(category=cat_code)
                bills_paid = bills.filter(status='paid').aggregate(total=Sum('amount'))['total'] or Decimal('0')
                bills_unpaid = bills.filter(status__in=['unpaid', 'scheduled']).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                bills_by_category[cat_code] = {
                    'name': category[1],
                    'paid': bills_paid,
                    'unpaid': bills_unpaid,
                    'total': bills_paid + bills_unpaid,
                    'percent_paid': int((bills_paid / (bills_paid + bills_unpaid)) * 100) if (bills_paid + bills_unpaid) > 0 else 0,
                    'bills': list(bills.values('id', 'name', 'amount', 'due_date', 'status'))
                }
            
            # Check if critical bills (housing, utilities) are paid
            housing_paid = bills_by_category.get('housing', {}).get('percent_paid', 0) == 100
            utilities_paid = bills_by_category.get('utilities', {}).get('percent_paid', 0) == 100
            transportation_paid = bills_by_category.get('transportation', {}).get('percent_paid', 0) == 100
            
            mode_data['essential_bills'] = bills_by_category
            mode_data['critical_bills_status'] = {
                'housing_paid': housing_paid,
                'utilities_paid': utilities_paid,
                'transportation_paid': transportation_paid,
                'all_critical_paid': housing_paid and utilities_paid and transportation_paid
            }
            
            # Get recent food expenses to estimate current spending
            recent_food_expenses = transactions.filter(
                transaction_type='EXPENSE',
                description__icontains='food', 
                date__gte=timezone.now() - timedelta(days=30)
            )
            
            # Alternative method if we have categories
            food_categories = transactions.filter(
                transaction_type='EXPENSE',
                category__category_type__in=['groceries', 'dining_out'],
                date__gte=timezone.now() - timedelta(days=30)
            )
            
            # Combine both methods
            all_food_expenses = list(recent_food_expenses) + list(food_categories)
            recent_food_total = sum(t.amount for t in all_food_expenses)
            
            mode_data['recent_food_spending'] = recent_food_total
            
        elif mode_name == "Survival Mode":
            mode_data = cls.check_survival_mode(user, transactions)
            
            # Add expense scheduler data for Survival Mode
            expense_schedule_data = cls.get_survival_expense_scheduler_data(user)
            mode_data['expense_scheduler'] = expense_schedule_data
            
        elif mode_name == "Stability Mode":
            mode_data = cls.check_stability_mode(user, transactions)
            
            # Add balance maintainer data for Stability Mode
            balance_maintainer_data = cls.get_stability_balance_maintainer_data(user)
            mode_data['balance_maintainer'] = balance_maintainer_data
            
        elif mode_name == "Saver Mode":
            mode_data = cls.check_saver_mode(user, transactions)
            
            # Add savings accelerator data for Saver Mode
            savings_accelerator_data = cls.get_saver_accelerator_data(user)
            mode_data['savings_accelerator'] = savings_accelerator_data
            
        elif mode_name == "Vacay Mode":
            mode_data = cls.check_vacay_mode(user, transactions)
            
            # Add freedom fund planner data for Vacay Mode
            freedom_fund_data = cls.get_vacay_freedom_fund_data(user)
            mode_data['freedom_fund'] = freedom_fund_data
        
        # Convert Decimal objects to float in mode_data
        mode_data = decimal_to_float(mode_data)
        
        return {
            'mode': mode,
            'current_data': {
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'savings': float(savings)
            },
            'mode_data': mode_data
        }
    
    @classmethod
    def get_mode_tips(cls, mode_name):
        """
        Get financial tips specific to a mode
        """
        # Mode-specific financial tips
        tips = {
            'lockdown_mode': [
                "Cut non-essential expenses immediately",
                "Contact creditors to negotiate payment plans",
                "Look for additional income sources",
                "Create a bare-minimum budget",
                "Prioritize essential bills (housing, utilities, food)"
            ],
            'survival_mode': [
                "Build a starter emergency fund of $1,000",
                "Use the 50/30/20 budgeting method",
                "Meal plan to reduce food costs",
                "Consider a temporary side job",
                "Eliminate unnecessary subscriptions"
            ],
            'stability_mode': [
                "Grow your emergency fund to 3-6 months of expenses",
                "Start contributing to retirement accounts",
                "Pay down high-interest debt",
                "Review and reduce recurring expenses",
                "Consider income-boosting opportunities"
            ],
            'saver_mode': [
                "Maximize retirement contributions",
                "Consider diversifying investments",
                "Review insurance coverage",
                "Set specific savings goals",
                "Automate savings transfers"
            ],
            'vacay_mode': [
                "Create a dedicated vacation fund",
                "Look for travel deals and off-peak pricing",
                "Consider travel rewards credit cards",
                "Set a daily vacation budget",
                "Balance vacation spending with long-term financial goals"
            ],
        }
        
        # Convert mode_name to the format used in the tips dictionary
        mode_key = mode_name.lower().replace(' ', '_')
        
        return tips.get(mode_key, [])
    
    @classmethod
    def get_survival_expense_scheduler_data(cls, user):
        """
        Get data for Survival Mode's expense scheduler feature
        """
        from main_app.models import SurvivalExpenseSchedule, Transaction
        from datetime import timedelta
        
        # Get upcoming bills
        today = timezone.now().date()
        end_of_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        upcoming_bills = SurvivalExpenseSchedule.objects.filter(
            user=user, 
            due_date__gte=today,
            due_date__lte=end_of_month,
            status__in=['pending', 'scheduled']
        ).order_by('due_date')
        
        # Get total of upcoming bills
        total_upcoming = sum(bill.amount for bill in upcoming_bills)
        
        # Get current available funds
        start_of_month = today.replace(day=1)
        current_month_income = Transaction.objects.filter(
            user=user,
            transaction_type='INCOME',
            date__gte=start_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        current_month_expenses = Transaction.objects.filter(
            user=user,
            transaction_type='EXPENSE',
            date__gte=start_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        available_funds = current_month_income - current_month_expenses
        
        # Calculate daily spending allowance after bills
        days_left = (end_of_month - today).days + 1
        funds_after_bills = available_funds - total_upcoming
        daily_allowance = funds_after_bills / days_left if days_left > 0 else Decimal('0')
        
        # Identify danger zones (days with multiple bills due)
        bill_dates = {}
        for bill in upcoming_bills:
            bill_date_str = bill.due_date.strftime('%Y-%m-%d')
            if bill_date_str not in bill_dates:
                bill_dates[bill_date_str] = {'date': bill.due_date, 'amount': Decimal('0'), 'bills': []}
            bill_dates[bill_date_str]['amount'] += bill.amount
            bill_dates[bill_date_str]['bills'].append({
                'id': bill.id,
                'name': bill.bill_name,
                'amount': float(bill.amount),
                'priority': bill.priority
            })
        
        # Convert to list and sort by date
        date_totals = [value for key, value in bill_dates.items()]
        date_totals.sort(key=lambda x: x['date'])
        
        # Identify danger zones (more than 25% of available funds due on a single day)
        danger_zones = []
        for date_data in date_totals:
            if available_funds > 0 and date_data['amount'] > (available_funds * Decimal('0.25')):
                danger_zones.append({
                    'date': date_data['date'].strftime('%Y-%m-%d'),
                    'amount': float(date_data['amount']),
                    'percentage': float(date_data['amount'] / available_funds * 100) if available_funds > 0 else 0,
                    'bills': date_data['bills']
                })
        
        # Generate optimal payment schedule (prioritize high priority bills first)
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for bill in upcoming_bills:
            bill_data = {
                'id': bill.id,
                'name': bill.bill_name,
                'amount': float(bill.amount),
                'due_date': bill.due_date.strftime('%Y-%m-%d'),
                'priority': bill.priority,
                'status': bill.status
            }
            
            if bill.priority == 'high':
                high_priority.append(bill_data)
            elif bill.priority == 'medium':
                medium_priority.append(bill_data)
            else:
                low_priority.append(bill_data)
        
        # Return combined data
        return {
            'upcoming_bills': {
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'low_priority': low_priority,
                'total': float(total_upcoming)
            },
            'available_funds': float(available_funds),
            'funds_after_bills': float(funds_after_bills),
            'daily_allowance': float(daily_allowance),
            'days_remaining': days_left,
            'danger_zones': danger_zones,
            'date_totals': [{
                'date': dt['date'].strftime('%Y-%m-%d'),
                'amount': float(dt['amount']),
                'bills': dt['bills']
            } for dt in date_totals]
        }
    
    @classmethod
    def get_stability_balance_maintainer_data(cls, user):
        """
        Get data for Stability Mode's balance maintainer feature
        """
        from main_app.models import Transaction, StabilityRatioTarget, CategorySpendingLimit
        from django.db.models import Sum
        from datetime import timedelta
        
        # Get current month's financials
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Get income and expenses for current month
        current_month_income = Transaction.objects.filter(
            user=user,
            transaction_type='INCOME',
            date__gte=start_of_month,
            date__lte=end_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        current_month_expenses = Transaction.objects.filter(
            user=user,
            transaction_type='EXPENSE',
            date__gte=start_of_month,
            date__lte=end_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Calculate current ratio
        current_ratio = Decimal('0')
        if current_month_income > 0:
            current_ratio = current_month_expenses / current_month_income
        
        # Get ratio history (last 5 months)
        monthly_ratios = []
        for i in range(5):
            month_start = (start_of_month - timedelta(days=i * 30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_income = Transaction.objects.filter(
                user=user,
                transaction_type='INCOME',
                date__gte=month_start,
                date__lte=month_end
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            month_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                date__gte=month_start,
                date__lte=month_end
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            month_ratio = Decimal('0')
            if month_income > 0:
                month_ratio = month_expenses / month_income
            
            monthly_ratios.append({
                'month': month_start.strftime('%b %Y'),
                'ratio': float(month_ratio),
                'income': float(month_income),
                'expenses': float(month_expenses)
            })
        
        # Calculate the average ratio from history to determine target
        valid_ratios = [r['ratio'] for r in monthly_ratios if r['ratio'] > 0]
        target_ratio = sum(valid_ratios) / len(valid_ratios) if valid_ratios else 0.7  # Default to 70% if no history
        
        # Get or create current month's target
        ratio_target, created = StabilityRatioTarget.objects.get_or_create(
            user=user,
            month=start_of_month,
            defaults={
                'income_target': current_month_income if current_month_income > 0 else Decimal('1000'),
                'expense_target': current_month_income * Decimal(str(target_ratio)) if current_month_income > 0 else Decimal('700'),
                'ratio_target': Decimal(str(target_ratio))
            }
        )
        
        # Calculate spending guardrails
        remaining_budget = ratio_target.income_target * ratio_target.ratio_target - current_month_expenses
        days_left_in_month = (end_of_month - today).days + 1
        daily_spending_limit = remaining_budget / days_left_in_month if days_left_in_month > 0 else Decimal('0')
        
        safe_spending_amount = remaining_budget * Decimal('0.9')  # 90% of remaining budget is considered "safe"
        warning_spending_amount = remaining_budget * Decimal('1.0')  # 100% of remaining budget is a warning (approaching limit)
        danger_spending_amount = remaining_budget * Decimal('1.1')  # 110% of remaining budget is danger (exceeding target ratio)
        
        # Get category spending limits
        category_limits = CategorySpendingLimit.objects.filter(
            user=user,
            month=start_of_month
        )
        
        category_spending = {}
        for limit in category_limits:
            # Get current spending for this category
            category_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                category=limit.category,
                date__gte=start_of_month,
                date__lte=end_of_month
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            # Calculate percentage of limit used
            percentage_used = 0
            if limit.limit_amount > 0:
                percentage_used = (category_expenses / limit.limit_amount) * 100
            
            category_spending[limit.category.id] = {
                'category_id': limit.category.id,
                'category_name': str(limit.category),
                'limit': float(limit.limit_amount),
                'spent': float(category_expenses),
                'remaining': float(limit.limit_amount - category_expenses),
                'percentage_used': float(percentage_used),
                'warning_threshold': limit.warning_threshold
            }
        
        # Return all data
        return {
            'current_month': {
                'income': float(current_month_income),
                'expenses': float(current_month_expenses),
                'ratio': float(current_ratio),
                'remaining_budget': float(remaining_budget),
                'is_on_target': current_ratio <= ratio_target.ratio_target
            },
            'target': {
                'ratio': float(ratio_target.ratio_target),
                'income': float(ratio_target.income_target),
                'expenses': float(ratio_target.expense_target)
            },
            'guardrails': {
                'daily_limit': float(daily_spending_limit),
                'safe_amount': float(safe_spending_amount),
                'warning_amount': float(warning_spending_amount),
                'danger_amount': float(danger_spending_amount),
                'days_remaining': days_left_in_month
            },
            'category_spending': list(category_spending.values()),
            'monthly_ratios': monthly_ratios
        }
    
    @classmethod
    def get_saver_accelerator_data(cls, user):
        """
        Get data for Saver Mode's savings accelerator feature
        """
        from main_app.models import Transaction, SavingsGoal, SavingsContribution
        from django.db.models import Sum
        from datetime import timedelta
        
        # Get current month's income
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        current_month_income = Transaction.objects.filter(
            user=user,
            transaction_type='INCOME',
            date__gte=start_of_month,
            date__lte=end_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Average income over last 3 months for more stable numbers
        three_months_ago = today - timedelta(days=90)
        avg_monthly_income = Transaction.objects.filter(
            user=user,
            transaction_type='INCOME',
            date__gte=three_months_ago
        ).values('date__month').annotate(monthly_sum=Sum('amount')).aggregate(Avg('monthly_sum'))['monthly_sum__avg'] or current_month_income
        
        if avg_monthly_income == 0:
            avg_monthly_income = Decimal('1000')  # Default for new users
            
        # Get all savings goals
        savings_goals = SavingsGoal.objects.filter(user=user).order_by('priority')
        
        # Calculate optimal savings allocation
        # Recommended savings percentage based on income
        if avg_monthly_income < 3000:
            recommended_savings_rate = Decimal('0.10')  # 10% for lower income
        elif avg_monthly_income < 6000:
            recommended_savings_rate = Decimal('0.15')  # 15% for middle income
        else:
            recommended_savings_rate = Decimal('0.20')  # 20% for higher income
            
        recommended_monthly_savings = avg_monthly_income * recommended_savings_rate
        
        # Get current month's savings contributions
        current_contributions = SavingsContribution.objects.filter(
            user=user,
            date__gte=start_of_month,
            date__lte=end_of_month
        )
        
        current_month_saved = sum(c.amount for c in current_contributions)
        
        # Get total savings by goal
        goal_data = []
        for goal in savings_goals:
            # Calculate time to goal completion based on current contribution rate
            monthly_contributions = SavingsContribution.objects.filter(
                user=user,
                goal=goal,
                date__gte=three_months_ago
            ).values('date__month').annotate(monthly_sum=Sum('amount'))
            
            avg_monthly_contribution = Decimal('0')
            if monthly_contributions:
                avg_monthly_contribution = sum(m['monthly_sum'] for m in monthly_contributions) / len(monthly_contributions)
            
            # Calculate months to complete, acceleration options
            months_to_complete = 0
            if avg_monthly_contribution > 0:
                months_to_complete = (goal.target_amount - goal.current_amount) / avg_monthly_contribution
            
            # Create acceleration options
            acceleration_options = []
            remaining = goal.target_amount - goal.current_amount
            
            if remaining > 0:
                for multiplier in [1.25, 1.5, 2.0]:
                    accelerated_contribution = avg_monthly_contribution * Decimal(str(multiplier))
                    if accelerated_contribution <= 0:
                        # If no contribution history, suggest a reasonable amount based on goal size
                        accelerated_contribution = remaining * Decimal('0.05')  # 5% of remaining
                        
                    accelerated_months = 0
                    if accelerated_contribution > 0:
                        accelerated_months = math.ceil(remaining / accelerated_contribution)
                        
                    months_saved = 0
                    if avg_monthly_contribution > 0:
                        months_saved = math.ceil(months_to_complete - accelerated_months)
                        
                    acceleration_options.append({
                        'multiplier': float(multiplier),
                        'monthly_amount': float(accelerated_contribution),
                        'months_to_complete': accelerated_months,
                        'months_saved': months_saved,
                        'percentage_of_income': float((accelerated_contribution / avg_monthly_income) * 100)
                    })
            
            # Get recent contributions
            recent_contributions = SavingsContribution.objects.filter(
                user=user,
                goal=goal
            ).order_by('-date')[:5]
            
            # Format goal data
            goal_data.append({
                'id': goal.id,
                'name': goal.name,
                'goal_type': goal.goal_type,
                'target_amount': float(goal.target_amount),
                'current_amount': float(goal.current_amount),
                'progress_percentage': goal.progress_percentage(),
                'target_date': goal.target_date.strftime('%Y-%m-%d') if goal.target_date else None,
                'icon': goal.icon,
                'monthly_target': float(goal.monthly_target()),
                'avg_monthly_contribution': float(avg_monthly_contribution),
                'months_to_complete': math.ceil(months_to_complete) if months_to_complete > 0 else None,
                'is_on_track': avg_monthly_contribution >= goal.monthly_target() if goal.monthly_target() > 0 else True,
                'acceleration_options': acceleration_options,
                'recent_contributions': [{
                    'date': c.date.strftime('%Y-%m-%d'),
                    'amount': float(c.amount),
                    'description': c.description
                } for c in recent_contributions]
            })
            
        # Calculate optimal allocation of the recommended monthly savings
        # Prioritize emergency fund first, then goals by priority
        optimal_allocation = {}
        remaining_savings = recommended_monthly_savings
        
        # Allocate to emergency fund goal first (if any)
        emergency_funds = [g for g in goal_data if g['goal_type'] == 'emergency']
        if emergency_funds and remaining_savings > 0:
            ef = emergency_funds[0]
            if ef['progress_percentage'] < 100:
                # Allocate up to half of recommended savings to emergency fund if not complete
                ef_allocation = min(remaining_savings * Decimal('0.5'), Decimal(str(ef['target_amount'] - ef['current_amount'])))
                optimal_allocation[ef['id']] = float(ef_allocation)
                remaining_savings -= ef_allocation
        
        # Allocate remaining based on priority
        prioritized_goals = sorted([g for g in goal_data if g['goal_type'] != 'emergency' and g['progress_percentage'] < 100], 
                                 key=lambda x: (x['priority'], x.get('months_to_complete', 999)))
                                 
        for goal in prioritized_goals:
            if remaining_savings <= 0:
                break
                
            goal_allocation = min(remaining_savings, Decimal(str(goal['target_amount'] - goal['current_amount'])))
            if goal_allocation > 0:
                optimal_allocation[goal['id']] = float(goal_allocation)
                remaining_savings -= goal_allocation
        
        # Return all data
        return {
            'income_data': {
                'current_month_income': float(current_month_income),
                'avg_monthly_income': float(avg_monthly_income),
                'recommended_savings_rate': float(recommended_savings_rate),
                'recommended_monthly_savings': float(recommended_monthly_savings),
                'current_month_saved': float(current_month_saved),
                'savings_gap': float(recommended_monthly_savings - current_month_saved)
            },
            'goals': goal_data,
            'optimal_allocation': optimal_allocation
        }
    
    @classmethod
    def get_vacay_freedom_fund_data(cls, user):
        """
        Get data for Vacay Mode's freedom fund planner feature
        """
        from main_app.models import Transaction, FreedomFundPlan, FreedomExpense
        from django.db.models import Sum, Count
        from datetime import timedelta
        
        # Get current month's financials
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Get income and expenses for current month
        current_month_income = Transaction.objects.filter(
            user=user,
            transaction_type='INCOME',
            date__gte=start_of_month,
            date__lte=end_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        current_month_expenses = Transaction.objects.filter(
            user=user,
            transaction_type='EXPENSE',
            date__gte=start_of_month,
            date__lte=end_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        current_savings = current_month_income - current_month_expenses
        
        # Get savings trend over the last 6 months
        six_months_ago = today - timedelta(days=180)
        monthly_savings = []
        
        for i in range(6):
            month_start = (start_of_month - timedelta(days=i * 30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_income = Transaction.objects.filter(
                user=user,
                transaction_type='INCOME',
                date__gte=month_start,
                date__lte=month_end
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            month_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                date__gte=month_start,
                date__lte=month_end
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            month_savings = month_income - month_expenses
            
            monthly_savings.append({
                'month': month_start.strftime('%b %Y'),
                'savings': float(month_savings),
                'income': float(month_income),
                'expenses': float(month_expenses)
            })
        
        # Calculate average monthly savings
        valid_savings = [ms['savings'] for ms in monthly_savings if ms['savings'] > 0]
        avg_monthly_savings = sum(valid_savings) / len(valid_savings) if valid_savings else 0
        
        # Get or create current month's freedom fund plan
        freedom_plan, created = FreedomFundPlan.objects.get_or_create(
            user=user,
            month=start_of_month,
            defaults={
                'discretionary_amount': max(current_savings, Decimal('0')),
                'freedom_allocation': max(current_savings * Decimal('0.3'), Decimal('0')),  # Default to 30% for freedom fund
                'savings_allocation': max(current_savings * Decimal('0.7'), Decimal('0')),  # Default to 70% for long-term savings
                'is_active': True
            }
        )
        
        # Get freedom expenses for current month
        freedom_expenses = FreedomExpense.objects.filter(
            user=user,
            date__gte=start_of_month,
            date__lte=end_of_month
        )
        
        # Calculate total spent from freedom fund
        total_freedom_spent = sum(fe.amount for fe in freedom_expenses)
        freedom_remaining = freedom_plan.freedom_allocation - total_freedom_spent
        
        # Calculate percentage used
        freedom_percentage_used = 0
        if freedom_plan.freedom_allocation > 0:
            freedom_percentage_used = (total_freedom_spent / freedom_plan.freedom_allocation) * 100
        
        # Group freedom expenses by category
        category_totals = {}
        for expense in freedom_expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = Decimal('0')
            category_totals[expense.category] += expense.amount
        
        # Format category data
        categories = []
        for category, total in category_totals.items():
            categories.append({
                'category': category,
                'total': float(total),
                'percentage': float((total / total_freedom_spent) * 100) if total_freedom_spent > 0 else 0
            })
        
        # Sort categories by total spent (descending)
        categories.sort(key=lambda x: x['total'], reverse=True)
        
        # Get recent freedom expenses
        recent_expenses = FreedomExpense.objects.filter(
            user=user
        ).order_by('-date')[:10]
        
        recent_expense_data = []
        for expense in recent_expenses:
            recent_expense_data.append({
                'id': expense.id,
                'date': expense.date.strftime('%Y-%m-%d'),
                'category': expense.category,
                'amount': float(expense.amount),
                'description': expense.description,
                'location': expense.location,
                'photo_url': expense.photo_url
            })
        
        # Calculate next month's recommended freedom allocation
        # Base on current month's trends
        next_month_discretionary = max(current_savings, Decimal('0'))
        
        # If current freedom fund was used up quickly, suggest increasing the allocation
        days_passed = (today - start_of_month).days + 1
        days_in_month = (end_of_month - start_of_month).days + 1
        
        freedom_adjustment = Decimal('1.0')  # Default no change
        
        if days_passed < days_in_month * 0.5 and freedom_percentage_used > 90:
            # Used up more than 90% of freedom fund in less than half the month
            freedom_adjustment = Decimal('1.3')  # Suggest 30% increase
        elif days_passed > days_in_month * 0.8 and freedom_percentage_used < 70:
            # Used less than 70% with most of month gone
            freedom_adjustment = Decimal('0.9')  # Suggest 10% decrease
        
        next_month_freedom = next_month_discretionary * Decimal('0.3') * freedom_adjustment
        next_month_savings = next_month_discretionary - next_month_freedom
        
        # Return all data
        return {
            'current_plan': {
                'month': freedom_plan.month.strftime('%B %Y'),
                'discretionary_amount': float(freedom_plan.discretionary_amount),
                'freedom_allocation': float(freedom_plan.freedom_allocation),
                'savings_allocation': float(freedom_plan.savings_allocation),
                'total_spent': float(total_freedom_spent),
                'remaining': float(freedom_remaining),
                'percentage_used': float(freedom_percentage_used)
            },
            'expenses': {
                'categories': categories,
                'recent': recent_expense_data
            },
            'next_month': {
                'estimated_discretionary': float(next_month_discretionary),
                'recommended_freedom': float(next_month_freedom),
                'recommended_savings': float(next_month_savings),
                'adjustment_factor': float(freedom_adjustment)
            },
            'savings_trend': monthly_savings,
            'avg_monthly_savings': float(avg_monthly_savings)
        } 