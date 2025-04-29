from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import ModeUnlock, Transaction, Category, Budget, BudgetItem, ModeHistory
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
        messages.success(request, f"🎉 Congratulations! You've unlocked {mode.name}: {mode.description}")
    
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
        # Check for mode unlocks every time transactions are viewed
        newly_unlocked = ModeService.update_user_modes(self.request.user)
        
        # Add notifications for newly unlocked modes
        for mode in newly_unlocked:
            messages.success(self.request, f"🎉 Congratulations! You've unlocked {mode.name}: {mode.description}")
            
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
            messages.success(self.request, f"🎉 Congratulations! You've unlocked {mode.name}: {mode.description}")
        
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
            messages.success(self.request, f"🎉 Congratulations! You've unlocked {mode.name}: {mode.description}")
        
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
            messages.success(self.request, f"🎉 Congratulations! You've unlocked {mode.name}: {mode.description}")
        
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
    mode_progression = [
        modes_data.get('lockdown_mode', {}),
        modes_data.get('survival_mode', {}),
        modes_data.get('stability_mode', {}),
        modes_data.get('saver_mode', {}),
        modes_data.get('vacay_mode', {})
    ]
    
    context = {
        'mode_progression': mode_progression,
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
    
    return render(request, 'mode_dashboard.html', context)


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

