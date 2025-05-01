from django.urls import path
from . import views
from .views import (

    unlocked_modes_view, TransactionList, TransactionCreate,
    TransactionUpdate, TransactionDelete,
    BudgetList, BudgetCreate, BudgetDetail, BudgetUpdate, BudgetDelete,
    BudgetItemUpdate, BudgetItemDelete,
    CategoryList,
    CategoryCreate,
    CategoryUpdate,
    CategoryDelete

)

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('modes/', unlocked_modes_view, name='unlocked_modes'),
    path('transactions/', TransactionList.as_view(), name='transaction_list'),
    path('transactions/create/', TransactionCreate.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/update/', TransactionUpdate.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', TransactionDelete.as_view(), name='transaction_delete'),
    path('register/', views.register, name='register'),
    path('budgets/', BudgetList.as_view(), name='budget_list'),
    path('budgets/create/', BudgetCreate.as_view(), name='budget_create'),
    path('budgets/<int:pk>/', BudgetDetail.as_view(), name='budget_detail'),
    path('budgets/<int:pk>/update/', BudgetUpdate.as_view(), name='budget_update'),
    path('budgets/<int:pk>/delete/', BudgetDelete.as_view(), name='budget_delete'),
    path('budget-items/<int:pk>/update/', BudgetItemUpdate.as_view(), name='budgetitem_update'),
    path('budget-items/<int:pk>/delete/', BudgetItemDelete.as_view(), name='budgetitem_delete'),
    path('categories/', CategoryList.as_view(), name='category_list'),
    path('categories/create/', CategoryCreate.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', CategoryUpdate.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDelete.as_view(), name='category_delete'),
    path('journey/', views.journey_map, name='journey_map'),
    path('journey/mode/<str:mode_name>/', views.mode_dashboard, name='mode_dashboard'),
    path('api/critical-spending/', views.save_critical_spending, name='save_critical_spending'),
    path('api/expense-schedule/', views.save_expense_schedule, name='save_expense_schedule'),
    path('api/stability-limits/', views.update_stability_limits, name='update_stability_limits'),
    path('api/savings-goal/', views.save_savings_goal, name='save_savings_goal'),
    path('api/savings-contribution/', views.save_savings_contribution, name='save_savings_contribution'),
    path('api/freedom-plan/', views.save_freedom_plan, name='save_freedom_plan'),
    path('api/freedom-expense/', views.save_freedom_expense, name='save_freedom_expense'),
]
