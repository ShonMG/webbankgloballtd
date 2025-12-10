from django.urls import path
from . import views

app_name = 'guarantees'

urlpatterns = [
    path('', views.guarantees_dashboard, name='guarantees_dashboard'),
]