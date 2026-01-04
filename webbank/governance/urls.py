from django.urls import path
from . import views

app_name = 'governance'

urlpatterns = [
    path('', views.VotingDashboardView.as_view(), name='dashboard'),
    path('resolution/<int:pk>/vote/', views.VoteResolutionView.as_view(), name='vote_resolution'),
]
