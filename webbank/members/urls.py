from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('', views.members_dashboard, name='members_dashboard'),
]