from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts_amor108'

urlpatterns = [
    path('signup/', views.Amor108SignUpView.as_view(), name='signup'),
    path('login/', views.Amor108LoginView.as_view(), name='login'),
    path('logout/', views.amor108_logout_view, name='logout'),
    path('dashboard/', views.amor108_dashboard, name='dashboard'),
    path('admin-panel/', views.amor108_admin_panel, name='admin_panel'),
    path('loan-option/', views.amor108_loan_option, name='amor108_loan_option'),
    path('profile-setup/', views.profile_setup_view, name='profile_setup'), # New URL for profile setup


    # Password reset views
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts_amor108/password_reset_form.html'),
        name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts_amor108/password_reset_done.html'),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts_amor108/password_reset_confirm.html'),
        name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts_amor108/password_reset_complete.html'),
        name='password_reset_complete'),

    # Password change views (for logged-in users)
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts_amor108/password_change_form.html'),
        name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts_amor108/password_change_done.html'),
        name='password_change_done'),
]