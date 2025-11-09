from django.urls import path
from .views import *

urlpatterns = [
    path('create/', ExpenseView.as_view(), name='create-expense'),
    path('get/', ExpenseView.as_view(), name='get-expense')
]
