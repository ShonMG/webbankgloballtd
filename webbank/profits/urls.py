from django.urls import path
from . import views

app_name = 'profits'

urlpatterns = [
    path('', views.member_profits_list, name='member_profits_list'),
    path('<int:pk>/withdraw/', views.withdraw_profit, name='withdraw_profit'),
    path('<int:pk>/reinvest/', views.reinvest_profit, name='reinvest_profit'),
]
