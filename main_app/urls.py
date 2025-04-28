from django.urls import path
from . import views
from .views import (
    unlocked_modes_view, TransactionList, TransactionCreate,
    BudgetList, BudgetCreate, BudgetDetail, BudgetUpdate, BudgetDelete,
    BudgetItemUpdate, BudgetItemDelete
)

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('modes/', unlocked_modes_view, name='unlocked_modes'),
    path('transactions/', TransactionList.as_view(), name='transaction_list'),
    path('transactions/create/', TransactionCreate.as_view(), name='transaction_create'),
    path('register/', views.register, name='register'),
    path('budgets/', BudgetList.as_view(), name='budget_list'),
    path('budgets/create/', BudgetCreate.as_view(), name='budget_create'),
    path('budgets/<int:pk>/', BudgetDetail.as_view(), name='budget_detail'),
    path('budgets/<int:pk>/update/', BudgetUpdate.as_view(), name='budget_update'),
    path('budgets/<int:pk>/delete/', BudgetDelete.as_view(), name='budget_delete'),
    path('budget-items/<int:pk>/update/', BudgetItemUpdate.as_view(), name='budgetitem_update'),
    path('budget-items/<int:pk>/delete/', BudgetItemDelete.as_view(), name='budgetitem_delete'),
]
