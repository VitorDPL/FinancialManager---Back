from django.urls import path
from .views import *

urlpatterns = [
    path('create/', ExpenseView.as_view(), name='create-expense'),
    path('get/', ExpenseView.as_view(), name='get-expense'),
    path('get-expenses-per-month/', ExpenseViewPerMonth.as_view(), name="get-expenses-per-month"),
    path('get-expenses-unique-month/', ExpensesViewUniqueMonth.as_view(), name="get-expenses-unique-month")
]
