from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('', views.support_dashboard, name='support_dashboard'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/new/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
]
