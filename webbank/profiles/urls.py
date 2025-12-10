from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_profile, name='create_profile'),
    path('application-submitted/', views.application_submitted, name='application_submitted'),
]
