from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.loans_dashboard, name='loans_dashboard'),
    path('my-loans/', views.my_loans, name='my_loans'),
    path('request/webbank/', views.webbank_loan_request, name='webbank_loan_request'),
    path('<int:pk>/repay/', views.repay_loan, name='repay_loan'),
    path('<int:loan_id>/repayment-schedule/', views.loan_repayment_schedule, name='loan_repayment_schedule'),
]