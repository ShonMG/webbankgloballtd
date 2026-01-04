from django.urls import path
from . import views

app_name = 'webbankboard'

urlpatterns = [
    path('apply/', views.apply_for_webbank, name='apply_for_webbank'),
]