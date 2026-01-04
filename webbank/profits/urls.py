from django.urls import path
from . import views

app_name = 'profits'

urlpatterns = [
    path('', views.ProfitDashboardView.as_view(), name='dashboard'), # New dashboard view
    path('<int:pk>/withdraw/', views.withdraw_profit, name='withdraw_profit'),
    path('<int:pk>/reinvest/', views.reinvest_profit, name='reinvest_profit'),
]
