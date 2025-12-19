from django.urls import path
from . import views

app_name = 'amor108'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('signin/', views.signin, name='signin'),
    
    # Main Dashboard (Profile)
    path('dashboard/', views.dashboard, name='dashboard'),

    # Individual Dashboard Sections
    path('dashboard/contributions/', views.dashboard_contributions, name='dashboard_contributions'),
    path('dashboard/shares/', views.dashboard_shares, name='dashboard_shares'),
    path('dashboard/loans/', views.dashboard_loans, name='dashboard_loans'),
    path('dashboard/my-loans/', views.dashboard_loans, name='my_loans'), # Added my_loans to point to the new loans dashboard
    path('dashboard/guarantees/', views.dashboard_guarantees, name='dashboard_guarantees'),
    path('dashboard/profits/', views.dashboard_placeholder, {'page_name': 'profits'}, name='dashboard_profits'),
    path('dashboard/investments/', views.dashboard_placeholder, {'page_name': 'investments'}, name='dashboard_investments'),
    path('dashboard/pools/', views.dashboard_placeholder, {'page_name': 'pools'}, name='dashboard_pools'),
    path('dashboard/voting/', views.dashboard_placeholder, {'page_name': 'voting'}, name='dashboard_voting'),
    path('dashboard/notifications/', views.dashboard_placeholder, {'page_name': 'notifications'}, name='dashboard_notifications'),
    path('dashboard/documents/', views.dashboard_placeholder, {'page_name': 'documents'}, name='dashboard_documents'),
    path('dashboard/exit/', views.dashboard_placeholder, {'page_name': 'exit'}, name='dashboard_exit'),
    path('dashboard/support/', views.dashboard_placeholder, {'page_name': 'support'}, name='dashboard_support'),
    path('dashboard/security/', views.dashboard_placeholder, {'page_name': 'security'}, name='dashboard_security'),
    path('dashboard/transparency/', views.dashboard_placeholder, {'page_name': 'transparency'}, name='dashboard_transparency'),

    # Functional pages
    path('pools/', views.pool_list, name='pool_list'),
    path('pools/<int:pool_id>/', views.pool_detail, name='pool_detail'),
    path('loan/request/', views.loan_request, name='loan_request'),
]
