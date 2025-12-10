from django.urls import path
from . import views

app_name = 'directors'

urlpatterns = [
    path('', views.directors_dashboard, name='directors_dashboard'),
    path('loan-approvals/', views.loan_approval_list, name='loan_approval_list'),
    path('loan-approvals/<int:loan_id>/', views.loan_approval_detail, name='loan_approval_detail'),
]