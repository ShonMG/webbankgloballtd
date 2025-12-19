from django.urls import path
from . import views

app_name = 'contributions'

urlpatterns = [
    path('make/', views.make_contribution, name='make_contribution'),
]
