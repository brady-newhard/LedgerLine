from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import ModeUnlock, Transaction, Budget, BudgetItem
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login
from .forms import UserRegistrationForm, BudgetForm, BudgetItemForm
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
    return render(request, 'home.html')

@login_required
def about(request):
    return render(request, 'about.html')

@login_required
def unlocked_modes_view(request):
    unlocked_modes = ModeUnlock.objects.filter(user=request.user, is_unlocked=True)
    return render(request, 'mode_unlock_list.html', {'modes': unlocked_modes})

# Stub transaction views
class TransactionList(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'main_app/transaction_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')

class TransactionCreate(LoginRequiredMixin, CreateView):
    model = Transaction
    template_name = 'main_app/transaction_form.html'
    fields = ['transaction_type', 'amount', 'description', 'date']
    success_url = reverse_lazy('transaction_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
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