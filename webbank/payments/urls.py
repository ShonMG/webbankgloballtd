from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('mpesa/callback/', views.mpesa_callback_view, name='mpesa_callback'),
    path('history/', views.PaymentTransactionListView.as_view(), name='payment_history'),
]