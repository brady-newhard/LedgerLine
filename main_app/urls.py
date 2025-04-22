from django.urls import path
from . import views
from .views import unlocked_modes_view, TransactionList, TransactionCreate

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('modes/', unlocked_modes_view, name='unlocked_modes'),
    path('transactions/', TransactionList.as_view(), name='transaction_list'),
    path('transactions/create/', TransactionCreate.as_view(), name='transaction_create'),
    path('register/', views.register, name='register'),
]
