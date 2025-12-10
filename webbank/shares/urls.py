from django.urls import path
from . import views

app_name = 'shares'

urlpatterns = [
    path('', views.shares_dashboard, name='shares_dashboard'),
    path('transactions-history/', views.transactions_history, name='transactions_history'),
    path('declare-dividend/', views.declare_dividend, name='declare_dividend'),
    path('dividends/', views.dividend_list, name='dividend_list'),
    path('approve-dividend/<int:dividend_id>/', views.approve_dividend, name='approve_dividend'),
]