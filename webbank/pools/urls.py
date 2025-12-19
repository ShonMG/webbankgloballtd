from django.urls import path
from . import views

app_name = 'pools'

urlpatterns = [
    path('', views.PoolListView.as_view(), name='pool_list'),
    path('create/', views.PoolCreateView.as_view(), name='pool_create'),
    path('<int:pk>/', views.PoolDetailView.as_view(), name='pool_detail'),
    path('<int:pk>/join/', views.PoolJoinView.as_view(), name='pool_join'),
]
