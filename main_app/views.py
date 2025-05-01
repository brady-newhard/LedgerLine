from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import ModeUnlock, Transaction, Category, Budget, BudgetItem, ModeHistory, CriticalSpending
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login
from .forms import UserRegistrationForm, CategoryForm, TransactionForm, BudgetForm, BudgetItemForm
from django.contrib import messages
from .services.mode_service import ModeService
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import models
import json

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def home(request):
    # Check for any newly unlocked modes
    newly_unlocked = ModeService.update_user_modes(request.user)
    
    # Show notifications for newly unlocked modes
    for mode in newly_unlocked:
        messages.success(request, f"Alert! You've unlocked {mode.name}: {mode.description}")
    
    return render(request, 'home.html')

@login_required
def about(request):
    return render(request, 'about.html')

@login_required
def unlocked_modes_view(request):
    # Force a refresh of all mode conditions
    ModeService.update_user_modes(request.user)
    
    # Get all modes (both locked and unlocked)
    all_modes = ModeUnlock.objects.filter(user=request.user).order_by('-is_unlocked', 'name')
    unlocked_modes = [mode for mode in all_modes if mode.is_unlocked]
    locked_modes = [mode for mode in all_modes if not mode.is_unlocked]
    
    # Check if we have any modes yet
    if not all_modes:
        # Initialize all possible modes for this user if none exist
        ModeService.check_all_modes(request.user)
        ModeService.update_user_modes(request.user)
        # Refresh the modes lists
        all_modes = ModeUnlock.objects.filter(user=request.user).order_by('-is_unlocked', 'name')
        unlocked_modes = [mode for mode in all_modes if mode.is_unlocked]
        locked_modes = [mode for mode in all_modes if not mode.is_unlocked]
    
    context = {
        'modes': unlocked_modes,
        'locked_modes': locked_modes,
        'all_modes': all_modes,
        'has_unlocked_modes': bool(unlocked_modes)
    }
    
    return render(request, 'mode_unlock_list.html', context)

# Transaction views
class TransactionList(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'main_app/transaction_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate monthly totals directly
        now = timezone.now()
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            last_day = now.replace(year=now.year + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            last_day = now.replace(month=now.month + 1, day=1) - timezone.timedelta(days=1)
            
        # Get transactions for the current month
        monthly_transactions = Transaction.objects.filter(
            user=self.request.user,
            date__gte=first_day,
            date__lte=last_day
        )
        
        # Calculate totals
        income = monthly_transactions.filter(transaction_type='INCOME').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        expenses = monthly_transactions.filter(transaction_type='EXPENSE').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        context['monthly_totals'] = {
            'income': income,
            'expenses': expenses,
            'net': income - expenses
        }
        
        return context

class TransactionCreate(LoginRequiredMixin, CreateView):
    model = Transaction
    template_name = 'main_app/transaction_form.html'
    success_url = reverse_lazy('transaction_list')
    
    def get_form_class(self):
        return TransactionForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user

        response = super().form_valid(form)
        
        # Check for mode unlocks after transaction is created
        newly_unlocked = ModeService.update_user_modes(self.request.user)
        
        # Add notifications for newly unlocked modes
        for mode in newly_unlocked:
            messages.success(self.request, f"Alert! You've unlocked {mode.name}: {mode.description}")
        
        return response

class TransactionUpdate(LoginRequiredMixin, UpdateView):
    model = Transaction
    template_name = 'main_app/transaction_form.html'
    success_url = reverse_lazy('transaction_list')
    
    def get_form_class(self):
        return TransactionForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Check for mode unlocks after transaction is updated
        newly_unlocked = ModeService.update_user_modes(self.request.user)
        
        # Add notifications for newly unlocked modes
        for mode in newly_unlocked:
            messages.success(self.request, f"Alert! You've unlocked {mode.name}: {mode.description}")
        
        return response

class TransactionDelete(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'main_app/transaction_confirm_delete.html'
    success_url = reverse_lazy('transaction_list')
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        
        # Check for mode unlocks after transaction is deleted
        newly_unlocked = ModeService.update_user_modes(self.request.user)
        
        # Add notifications for newly unlocked modes
        for mode in newly_unlocked:
            messages.success(self.request, f"Alert! You've unlocked {mode.name}: {mode.description}")
        
        return response

@login_required
def journey_map(request):
    """
    Display the user's financial mode journey map
    """
    # Get all mode data with current statuses
    modes_data = ModeService.check_all_modes(request.user)
    
    # Get historical data
    mode_history = ModeService.get_user_mode_history(request.user)
    
    # Organize modes in their progression order
    modes = [
        modes_data.get('lockdown_mode', {}),
        modes_data.get('survival_mode', {}),
        modes_data.get('stability_mode', {}),
        modes_data.get('saver_mode', {}),
        modes_data.get('vacay_mode', {})
    ]
    
    context = {
        'modes': modes,
        'mode_history': mode_history,
        'current_tab': 'journey'
    }
    
    return render(request, 'journey_map.html', context)

@login_required
def mode_dashboard(request, mode_name):
    """
    Display detailed dashboard for a specific mode
    """
    # Get detailed data for the specific mode
    mode_data = ModeService.get_mode_dashboard_data(request.user, mode_name)
    
    # Get mode-specific financial tips
    mode_tips = ModeService.get_mode_tips(mode_name)
    
    context = {
        'mode_data': mode_data,
        'mode_tips': mode_tips,
        'current_tab': 'journey'
    }
    
    return render(request, 'main_app/mode_dashboard.html', context)


class CategoryList(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by('category_type')

class CategoryCreate(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)

class BudgetList(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'main_app/budget_list.html'
    context_object_name = 'budgets'
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

class BudgetCreate(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'main_app/budget_form.html'
    success_url = reverse_lazy('budget_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class BudgetDetail(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'main_app/budget_detail.html'
    context_object_name = 'budget'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['form'] = BudgetItemForm()
        return context
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = BudgetItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.budget = self.object
            item.save()
            return redirect('budget_detail', pk=self.object.pk)
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

class BudgetUpdate(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'main_app/budget_form.html'
    success_url = reverse_lazy('budget_list')
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

class BudgetDelete(LoginRequiredMixin, DeleteView):
    model = Budget
    template_name = 'main_app/budget_confirm_delete.html'
    success_url = reverse_lazy('budget_list')
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

class BudgetItemUpdate(LoginRequiredMixin, UpdateView):
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = 'main_app/budgetitem_form.html'
    
    def get_success_url(self):
        return reverse_lazy('budget_detail', kwargs={'pk': self.object.budget.pk})
    
    def get_queryset(self):
        return BudgetItem.objects.filter(budget__user=self.request.user)

class BudgetItemDelete(LoginRequiredMixin, DeleteView):
    model = BudgetItem
    template_name = 'main_app/budgetitem_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('budget_detail', kwargs={'pk': self.object.budget.pk})
    
    def get_queryset(self):
        return BudgetItem.objects.filter(budget__user=self.request.user)
class CategoryUpdate(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)

class CategoryDelete(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        transaction_count = Transaction.objects.filter(category=category).count()
        context['transaction_count'] = transaction_count
        return context
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        transaction_count = Transaction.objects.filter(category=category).count()
        if transaction_count > 0:
            messages.warning(request, f'Category deleted. {transaction_count} transactions were updated to have no category.')
        else:
            messages.success(request, 'Category deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
@require_POST
def save_critical_spending(request):
    """
    Save a critical spending entry for Lockdown Mode tracking
    """
    try:
        data = json.loads(request.body)
        category = data.get('category')
        amount = data.get('amount')
        notes = data.get('notes', '')
        
        # Validate required fields
        if not category or not amount:
            return JsonResponse({'error': 'Category and amount are required'}, status=400)
        
        # Map front-end category names to model choices
        category_map = {
            'groceries': 'basic_groceries',
            'meals': 'essential_meals',
            'emergency': 'emergency_food'
        }
        
        db_category = category_map.get(category)
        if not db_category:
            return JsonResponse({'error': 'Invalid category'}, status=400)
        
        # Create and save the critical spending entry
        critical_spending = CriticalSpending(
            user=request.user,
            category=db_category,
            amount=amount,
            notes=notes
        )
        critical_spending.save()
        
        # Get the total spent for this category in the current month
        from django.utils import timezone
        from datetime import datetime
        
        first_day = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_category_spent = CriticalSpending.objects.filter(
            user=request.user,
            category=db_category,
            date__gte=first_day
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return JsonResponse({
            'success': True,
            'id': critical_spending.id,
            'category': critical_spending.get_category_display(),
            'amount': float(critical_spending.amount),
            'total_spent': float(total_category_spent)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def save_expense_schedule(request):
    """
    Save an expense schedule entry for Survival Mode
    """
    try:
        data = json.loads(request.body)
        bill_name = data.get('bill_name')
        amount = data.get('amount')
        due_date = data.get('due_date')
        priority = data.get('priority', 'medium')
        status = data.get('status', 'pending')
        category_id = data.get('category_id')
        notes = data.get('notes', '')
        
        # Validate required fields
        if not bill_name or not amount or not due_date:
            return JsonResponse({'error': 'Bill name, amount, and due date are required'}, status=400)
        
        # Convert due_date from string to date object
        try:
            parsed_due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid due date format. Use YYYY-MM-DD'}, status=400)
        
        # Get category if provided
        category = None
        if category_id:
            category = Category.objects.filter(id=category_id, user=request.user).first()
        
        # Create and save the expense schedule entry
        expense_schedule = SurvivalExpenseSchedule(
            user=request.user,
            bill_name=bill_name,
            amount=amount,
            due_date=parsed_due_date,
            priority=priority,
            status=status,
            category=category,
            notes=notes
        )
        expense_schedule.save()
        
        # Get updated scheduler data
        from .services.mode_service import ModeService
        scheduler_data = ModeService.get_survival_expense_scheduler_data(request.user)
        
        return JsonResponse({
            'success': True,
            'id': expense_schedule.id,
            'bill_name': expense_schedule.bill_name,
            'amount': float(expense_schedule.amount),
            'due_date': expense_schedule.due_date.strftime('%Y-%m-%d'),
            'scheduler_data': scheduler_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def update_stability_limits(request):
    """
    Update or create category spending limits for Stability Mode
    """
    try:
        data = json.loads(request.body)
        category_limits = data.get('category_limits', [])
        
        if not category_limits:
            return JsonResponse({'error': 'No category limits provided'}, status=400)
        
        # Get current month
        today = timezone.now().date()
        current_month = today.replace(day=1)
        
        results = []
        for limit_data in category_limits:
            category_id = limit_data.get('category_id')
            limit_amount = limit_data.get('limit_amount')
            warning_threshold = limit_data.get('warning_threshold', 80)
            
            if not category_id or limit_amount is None:
                continue
            
            # Get category
            category = Category.objects.filter(id=category_id, user=request.user).first()
            if not category:
                continue
            
            # Update or create limit
            limit, created = CategorySpendingLimit.objects.update_or_create(
                user=request.user,
                category=category,
                month=current_month,
                defaults={
                    'limit_amount': limit_amount,
                    'warning_threshold': warning_threshold
                }
            )
            
            results.append({
                'id': limit.id,
                'category_id': category.id,
                'category_name': str(category),
                'limit_amount': float(limit.limit_amount),
                'warning_threshold': limit.warning_threshold,
                'created': created
            })
        
        # Get updated balance maintainer data
        from .services.mode_service import ModeService
        maintainer_data = ModeService.get_stability_balance_maintainer_data(request.user)
        
        return JsonResponse({
            'success': True,
            'results': results,
            'maintainer_data': maintainer_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def save_savings_goal(request):
    """
    Create or update a savings goal for Saver Mode
    """
    try:
        data = json.loads(request.body)
        goal_id = data.get('goal_id')  # Only for updates
        name = data.get('name')
        goal_type = data.get('goal_type', 'other')
        target_amount = data.get('target_amount')
        current_amount = data.get('current_amount', 0)
        target_date_str = data.get('target_date')
        priority = data.get('priority', 1)
        icon = data.get('icon', '💰')
        notes = data.get('notes', '')
        
        # Validate required fields
        if not name or target_amount is None:
            return JsonResponse({'error': 'Name and target amount are required'}, status=400)
        
        # Convert target_date from string to date object if provided
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid target date format. Use YYYY-MM-DD'}, status=400)
        
        # Update existing goal or create new one
        if goal_id:
            # Update existing goal
            goal = SavingsGoal.objects.filter(id=goal_id, user=request.user).first()
            if not goal:
                return JsonResponse({'error': 'Goal not found'}, status=404)
            
            goal.name = name
            goal.goal_type = goal_type
            goal.target_amount = target_amount
            goal.current_amount = current_amount
            goal.target_date = target_date
            goal.priority = priority
            goal.icon = icon
            goal.notes = notes
            
            # Check if goal is completed
            if current_amount >= target_amount and not goal.is_completed:
                goal.is_completed = True
                goal.completed_date = timezone.now().date()
            elif current_amount < target_amount and goal.is_completed:
                goal.is_completed = False
                goal.completed_date = None
                
            goal.save()
        else:
            # Create new goal
            goal = SavingsGoal.objects.create(
                user=request.user,
                name=name,
                goal_type=goal_type,
                target_amount=target_amount,
                current_amount=current_amount,
                target_date=target_date,
                priority=priority,
                icon=icon,
                notes=notes,
                is_completed=current_amount >= target_amount,
                completed_date=timezone.now().date() if current_amount >= target_amount else None
            )
        
        # Get updated savings accelerator data
        from .services.mode_service import ModeService
        accelerator_data = ModeService.get_saver_accelerator_data(request.user)
        
        return JsonResponse({
            'success': True,
            'id': goal.id,
            'name': goal.name,
            'target_amount': float(goal.target_amount),
            'current_amount': float(goal.current_amount),
            'progress_percentage': goal.progress_percentage(),
            'accelerator_data': accelerator_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def save_savings_contribution(request):
    """
    Record a contribution to a savings goal
    """
    try:
        data = json.loads(request.body)
        goal_id = data.get('goal_id')
        amount = data.get('amount')
        date_str = data.get('date')
        description = data.get('description', '')
        
        # Validate required fields
        if amount is None:
            return JsonResponse({'error': 'Amount is required'}, status=400)
        
        # Convert date from string to date object if provided
        contrib_date = timezone.now().date()
        if date_str:
            try:
                contrib_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        # Get goal if provided
        goal = None
        if goal_id:
            goal = SavingsGoal.objects.filter(id=goal_id, user=request.user).first()
            if not goal:
                return JsonResponse({'error': 'Goal not found'}, status=404)
        
        # Create contribution
        contribution = SavingsContribution.objects.create(
            user=request.user,
            goal=goal,
            amount=amount,
            date=contrib_date,
            description=description
        )
        
        # Update goal current amount if applicable
        if goal:
            goal.current_amount += Decimal(str(amount))
            
            # Check if goal is completed
            if goal.current_amount >= goal.target_amount and not goal.is_completed:
                goal.is_completed = True
                goal.completed_date = timezone.now().date()
                
            goal.save()
        
        # Get updated savings accelerator data
        from .services.mode_service import ModeService
        accelerator_data = ModeService.get_saver_accelerator_data(request.user)
        
        return JsonResponse({
            'success': True,
            'id': contribution.id,
            'amount': float(contribution.amount),
            'date': contribution.date.strftime('%Y-%m-%d'),
            'goal_id': goal.id if goal else None,
            'goal_current_amount': float(goal.current_amount) if goal else None,
            'goal_progress_percentage': goal.progress_percentage() if goal else None,
            'accelerator_data': accelerator_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def save_freedom_plan(request):
    """
    Create or update a freedom fund plan for Vacay Mode
    """
    try:
        data = json.loads(request.body)
        discretionary_amount = data.get('discretionary_amount')
        freedom_allocation = data.get('freedom_allocation')
        savings_allocation = data.get('savings_allocation')
        notes = data.get('notes', '')
        
        # Validate required fields
        if discretionary_amount is None or freedom_allocation is None or savings_allocation is None:
            return JsonResponse({'error': 'Discretionary amount, freedom allocation, and savings allocation are required'}, status=400)
        
        # Get current month
        today = timezone.now().date()
        current_month = today.replace(day=1)
        
        # Update or create plan
        plan, created = FreedomFundPlan.objects.update_or_create(
            user=request.user,
            month=current_month,
            defaults={
                'discretionary_amount': discretionary_amount,
                'freedom_allocation': freedom_allocation,
                'savings_allocation': savings_allocation,
                'notes': notes,
                'is_active': True
            }
        )
        
        # Get updated freedom fund data
        from .services.mode_service import ModeService
        freedom_data = ModeService.get_vacay_freedom_fund_data(request.user)
        
        return JsonResponse({
            'success': True,
            'id': plan.id,
            'month': plan.month.strftime('%b %Y'),
            'discretionary_amount': float(plan.discretionary_amount),
            'freedom_allocation': float(plan.freedom_allocation),
            'savings_allocation': float(plan.savings_allocation),
            'freedom_data': freedom_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def save_freedom_expense(request):
    """
    Record a freedom fund expense for Vacay Mode
    """
    try:
        data = json.loads(request.body)
        category = data.get('category', 'other')
        amount = data.get('amount')
        date_str = data.get('date')
        description = data.get('description', '')
        location = data.get('location', '')
        photo_url = data.get('photo_url', '')
        
        # Validate required fields
        if amount is None or not description:
            return JsonResponse({'error': 'Amount and description are required'}, status=400)
        
        # Convert date from string to date object if provided
        expense_date = timezone.now().date()
        if date_str:
            try:
                expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        # Get current month's plan
        today = timezone.now().date()
        current_month = today.replace(day=1)
        plan = FreedomFundPlan.objects.filter(user=request.user, month=current_month).first()
        
        # Create expense
        expense = FreedomExpense.objects.create(
            user=request.user,
            plan=plan,
            category=category,
            amount=amount,
            date=expense_date,
            description=description,
            location=location,
            photo_url=photo_url
        )
        
        # Get updated freedom fund data
        from .services.mode_service import ModeService
        freedom_data = ModeService.get_vacay_freedom_fund_data(request.user)
        
        return JsonResponse({
            'success': True,
            'id': expense.id,
            'category': expense.category,
            'amount': float(expense.amount),
            'date': expense.date.strftime('%Y-%m-%d'),
            'description': expense.description,
            'freedom_data': freedom_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

