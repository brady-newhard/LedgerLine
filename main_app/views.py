from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import ModeUnlock, Transaction, Category
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login
from .forms import UserRegistrationForm, CategoryForm, TransactionForm
from django.contrib import messages

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
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')

class TransactionCreate(LoginRequiredMixin, CreateView):
    model = Transaction
    template_name = 'transactions/transaction_form.html'
    success_url = reverse_lazy('transaction_list')
    
    def get_form_class(self):
        return TransactionForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Transaction created successfully!')
        return super().form_valid(form)

class CategoryList(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by('name')

class CategoryCreate(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)

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

