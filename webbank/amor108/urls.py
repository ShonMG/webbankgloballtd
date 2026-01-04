from django.urls import path, include # Import include
from . import views
from profits import views as profits_views # Import profits views

app_name = 'amor108'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('signin/', views.signin, name='signin'),
    
    # Main Dashboard (Home)
    path('dashboard/', views.dashboard_home, name='dashboard'),

    # Profile page
    path('dashboard/profile/', views.dashboard_profile, name='dashboard_profile'),

    # Individual Dashboard Sections
    path('dashboard/contributions/', views.dashboard_contributions, name='dashboard_contributions'),
    path('dashboard/shares/', views.dashboard_shares, name='dashboard_shares'),
    path('dashboard/loans/', views.dashboard_loans, name='dashboard_loans'),
    path('dashboard/my-loans/', views.dashboard_loans, name='my_loans'), # Added my_loans to point to the new loans dashboard
    path('dashboard/guarantees/', views.dashboard_guarantees, name='dashboard_guarantees'),
    path('dashboard/guarantees/accept/<int:guarantee_id>/', views.accept_guarantee, name='accept_guarantee'),
    path('dashboard/guarantees/reject/<int:guarantee_id>/', views.reject_guarantee, name='reject_guarantee'),
    path('dashboard/profits/', profits_views.ProfitDashboardView.as_view(), name='dashboard_profits'), # Link to actual ProfitDashboardView
    path('dashboard/investments/', views.dashboard_investments, name='dashboard_investments'),
    path('dashboard/pools/', views.dashboard_pools, name='dashboard_pools'),
    path('dashboard/voting/', views.dashboard_voting, name='dashboard_voting'),
    path('dashboard/notifications/', views.dashboard_notifications, name='dashboard_notifications'),
    path('dashboard/documents/', views.dashboard_documents, name='dashboard_documents'),
    path('dashboard/exit/', views.dashboard_exit, name='dashboard_exit'),
    path('dashboard/exit/request/', views.request_exit, name='request_exit'),
    path('pending_approval/', views.pending_approval_view, name='pending_approval'),
    path('dashboard/support/', views.dashboard_support, name='dashboard_support'),
    path('dashboard/security/', views.dashboard_security, name='dashboard_security'),
    path('dashboard/transparency/', views.dashboard_transparency, name='dashboard_transparency'),

    # Functional pages
    path('pools/', views.pool_list, name='pool_list'),
    path('pools/<int:pool_id>/', views.pool_detail, name='pool_detail'),
    path('loan/request/', views.loan_request, name='loan_request'),
]
