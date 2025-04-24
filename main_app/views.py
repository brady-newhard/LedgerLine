from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import ModeUnlock, Transaction
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegistrationForm, TransactionForm
from .services import ModeService

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
    unlocked_modes = ModeUnlock.objects.filter(user=request.user, is_unlocked=True)
    return render(request, 'mode_unlock_list.html', {'modes': unlocked_modes})

class TransactionList(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'main_app/transaction_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = context['transactions']
        
        total_income = sum(t.amount for t in transactions if t.transaction_type == 'INCOME')
        total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'EXPENSE')
        net_balance = total_income - total_expenses
        
        context['total_income'] = total_income
        context['total_expenses'] = total_expenses
        context['net_balance'] = net_balance
        
        return context

class TransactionCreate(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'main_app/transaction_form.html'
    success_url = reverse_lazy('transaction_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

class TransactionDelete(LoginRequiredMixin, DeleteView):
    model = Transaction
    success_url = reverse_lazy('transaction_list')
    template_name = 'main_app/transaction_confirm_delete.html'
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
