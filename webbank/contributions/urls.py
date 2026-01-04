from django.urls import path
from . import views

app_name = 'contributions'

urlpatterns = [
    path('', views.ContributionDashboardView.as_view(), name='dashboard'), # New dashboard view for contributions
    path('stk-push/', views.make_contribution, name='stk_push_initiate'), # Renamed for STK Push initiation
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'), # New URL for M-Pesa callback simulation
]
