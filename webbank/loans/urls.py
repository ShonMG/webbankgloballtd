from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.loans_dashboard, name='loans_dashboard'),
    path('my-loans/', views.my_loans, name='my_loans'),
]