from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
import math

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
        Get detailed dashboard data for a specific mode
        """
        from main_app.models import ModeUnlock, ModeHistory
        
        # Get the mode details
        mode = ModeUnlock.objects.filter(user=user, name=mode_name).first()
        
        if not mode:
            return None
        
        # Get mode history for this specific mode
        history = ModeHistory.objects.filter(
            user=user, 
            mode_name=mode_name
        ).order_by('-timestamp')
        
        # Get current mode status
        all_modes = cls.check_all_modes(user)
        current_mode_data = all_modes.get(mode_name.lower().replace(' ', '_'), {})
        
        # Combine all data
        dashboard_data = {
            'mode': mode,
            'history': history,
            'current_data': current_mode_data,
            'progress_history': [
                {'date': event.timestamp, 'progress': event.progress_percentage} 
                for event in history.filter(status_change='progress')
            ]
        }
        
        return dashboard_data
    
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