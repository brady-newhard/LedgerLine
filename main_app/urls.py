from django.urls import path, include
from . import views
from .views import (
    unlocked_modes_view, TransactionList, TransactionCreate,
<<<<<<< HEAD
    TransactionUpdate, TransactionDelete,
    BudgetList, BudgetCreate, BudgetDetail, BudgetUpdate, BudgetDelete,
    BudgetItemUpdate, BudgetItemDelete,
=======
    YearListView, MonthListView, BudgetDetailView,
>>>>>>> a310664 (fix routes, database and migrations)
    CategoryList,
    CategoryCreate,
    CategoryUpdate,
    CategoryDelete,
    IncomeList,
    IncomeCreate,
    IncomeUpdate,
    IncomeDelete,
    BudgetIncomeCreate,
    BudgetListView,
    BudgetItemListView,
    BudgetItemUpdate,
    BudgetItemDelete,
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
    path('calendar/', views.YearListView.as_view(), name='year_list'),
    path('calendar/<int:year>/', views.MonthListView.as_view(), name='month_list'),
    path('calendar/<int:year>/<int:month>/', BudgetListView.as_view(), name='budget_list'),
    path('calendar/<int:year>/<int:month>/<int:budget_id>/', views.BudgetDetailView.as_view(), name='budget_detail'),
    path('categories/', CategoryList.as_view(), name='category_list'),
    path('categories/create/', CategoryCreate.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', CategoryUpdate.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDelete.as_view(), name='category_delete'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('journey/', views.journey_map, name='journey_map'),
<<<<<<< HEAD
    path('journey/mode/<str:mode_name>/', views.mode_dashboard, name='mode_dashboard'),
    path('api/critical-spending/', views.save_critical_spending, name='save_critical_spending'),
    path('api/expense-schedule/', views.save_expense_schedule, name='save_expense_schedule'),
    path('api/stability-limits/', views.update_stability_limits, name='update_stability_limits'),
    path('api/savings-goal/', views.save_savings_goal, name='save_savings_goal'),
    path('api/savings-contribution/', views.save_savings_contribution, name='save_savings_contribution'),
    path('api/freedom-plan/', views.save_freedom_plan, name='save_freedom_plan'),
    path('api/freedom-expense/', views.save_freedom_expense, name='save_freedom_expense'),
=======
    path('modes/<str:mode_name>/dashboard/', views.mode_dashboard, name='mode_dashboard'),
    path('incomes/', IncomeList.as_view(), name='income_list'),
    path('budgets/<int:year>/<int:month>/income/add/', views.IncomeCreate.as_view(), name='income_create'),
    path('incomes/<int:pk>/edit/', IncomeUpdate.as_view(), name='income_update'),
    path('incomes/<int:pk>/delete/', IncomeDelete.as_view(), name='income_delete'),
    path('budgets/<int:budget_pk>/add_income/', BudgetIncomeCreate.as_view(), name='budget_add_income'),
    path('budgets/create/<int:year>/<int:month>/', views.BudgetCreate.as_view(), name='budget_create'),
    path('budgets/<int:pk>/edit/', views.BudgetUpdate.as_view(), name='budget_update'),
    path('budgets/<int:pk>/delete/', views.BudgetDelete.as_view(), name='budget_delete'),
    path('budgets/<int:pk>/items/', BudgetItemListView.as_view(), name='budgetitem_list'),
    path('budgetitem/<int:pk>/edit/', BudgetItemUpdate.as_view(), name='budgetitem_update'),
    path('budgetitem/<int:pk>/delete/', BudgetItemDelete.as_view(), name='budgetitem_delete'),
>>>>>>> a310664 (fix routes, database and migrations)
]
