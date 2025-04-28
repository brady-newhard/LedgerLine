from django.urls import path
from . import views
from .views import (
    unlocked_modes_view, 
    TransactionList, 
    TransactionCreate,
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
    path('register/', views.register, name='register'),
    
    # Category URLs
    path('categories/', CategoryList.as_view(), name='category_list'),
    path('categories/create/', CategoryCreate.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', CategoryUpdate.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDelete.as_view(), name='category_delete'),
]
