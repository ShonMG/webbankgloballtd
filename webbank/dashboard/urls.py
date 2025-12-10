from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.main_dashboard, name='main_dashboard'),
]