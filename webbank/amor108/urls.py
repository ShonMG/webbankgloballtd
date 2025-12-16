from django.urls import path
from . import views

app_name = 'amor108'

urlpatterns = [
    path('', views.index, name='index'),
    path('pools/', views.pool_list, name='pool_list'),
    path('pools/<int:pool_id>/', views.pool_detail, name='pool_detail'),
    path('loan/request/', views.loan_request, name='loan_request'),
    path('contribution/make/', views.make_contribution, name='make_contribution'),
    path('signin/', views.signin, name='signin'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
