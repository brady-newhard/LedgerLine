from django.contrib import admin

from .models import (
    ModeUnlock, Transaction, Category, Budget, Calendar,
    BudgetItem, Income, ModeHistory, CriticalSpending,
    EssentialBill, SurvivalExpenseSchedule, CategorySpendingLimit,
    SavingsGoal, FreedomFundPlan, FreedomExpense, SavingsContribution,
    StabilityRatioTarget
)

admin.site.register(ModeUnlock)
admin.site.register(Transaction)
admin.site.register(Category)
admin.site.register(Budget)
admin.site.register(Calendar)
admin.site.register(BudgetItem)
admin.site.register(Income)
admin.site.register(ModeHistory)
admin.site.register(CriticalSpending)
admin.site.register(EssentialBill)
admin.site.register(SurvivalExpenseSchedule)
admin.site.register(CategorySpendingLimit)
admin.site.register(SavingsGoal)
admin.site.register(FreedomFundPlan)
admin.site.register(FreedomExpense)
admin.site.register(SavingsContribution)
admin.site.register(StabilityRatioTarget)


