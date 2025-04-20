from django.shortcuts import render, redirect
from .models import ModeUnlock, Transaction
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

@login_required
def unlocked_modes_view(request):
    unlocked_modes = ModeUnlock.objects.filter(user=request.user, is_unlocked=True)
    return render(request, 'mode_unlock_list.html', {'modes': unlocked_modes})

# Stub transaction views
class TransactionList(LoginRequiredMixin, ListView):
    model = Transaction
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')

class TransactionCreate(LoginRequiredMixin, CreateView):
    model = Transaction
    fields = ['transaction_type', 'amount', 'description', 'date']
    success_url = reverse_lazy('transaction_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

