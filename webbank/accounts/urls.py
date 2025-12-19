from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('password-change/', views.password_change, name='password_change'),
    path('prolink-network/', views.prolink_network_detail, name='prolink_network_detail'),
    path('amor-108-inv/', views.amor_108_inv_detail, name='amor_108_inv_detail'),
    path('loan-options/', views.loan_options, name='loan_options'),
]