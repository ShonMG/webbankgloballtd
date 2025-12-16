from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('founder-dashboard/', views.founder_dashboard, name='founder_dashboard'),
    path('loan-approvals/', views.loan_approval_list, name='loan_approval_list'),
    path('loan-approvals/<int:loan_id>/', views.loan_approval_detail, name='loan_approval_detail'),
    path('loan-config/', views.loan_config_panel, name='loan_config_panel'),
    path('loan-config/add/', views.loan_type_form, name='loan_type_create'),
    path('loan-config/edit/<int:pk>/', views.loan_type_form, name='loan_type_edit'),
    path('share-config/', views.share_config_panel, name='share_config_panel'),
    path('system-config/', views.system_config_panel, name='system_config_panel'),
    
    # User Management URLs
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('users/deactivate/<int:pk>/', views.user_deactivate, name='user_deactivate'),
    path('users/reset-password/<int:pk>/', views.user_reset_password, name='user_reset_password'),

    # Notification Management URLs
    path('notifications/settings/', views.notification_settings_panel, name='notification_settings_panel'),
    path('notifications/templates/', views.notification_template_list, name='notification_template_list'),
    path('notifications/templates/edit/<int:pk>/', views.notification_template_edit, name='notification_template_edit'),

    # Reporting URLs
    path('reports/', views.reporting_dashboard, name='reporting_dashboard'),
    path('reports/loan-performance/', views.loan_performance_report, name='loan_performance_report'),
    path('reports/member-growth/', views.member_growth_report, name='member_growth_report'),
    path('reports/share-value-trends/', views.share_value_trends_report, name='share_value_trends_report'),
    path('reports/financial-statements/', views.financial_statements_report, name='financial_statements_report'),

    # Audit & Compliance URLs
    path('audit-log/', views.audit_log_list, name='audit_log_list'),

    # Member Approval URLs
    path('members/pending/', views.pending_members, name='pending_members'),
    path('members/approve/<int:profile_id>/', views.approve_member, name='approve_member'),
    path('members/reject/<int:profile_id>/', views.reject_member, name='reject_member'),

    # Amor108 Member Approval URLs
    path('amor108/pending/', views.pending_amor108_members, name='pending_amor108_members'),
    path('amor108/approve/<int:member_id>/', views.approve_amor108_member, name='approve_amor108_member'),
    path('amor108/reject/<int:member_id>/', views.reject_amor108_member, name='reject_amor108_member'),
]