from django.urls import path
from .views import *

urlpatterns = [
    path('create/', CategoryCreateView.as_view(), name='create'),
    path('read/', CategoryListView.as_view(), name='category-list')
]
