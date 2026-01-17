from django.contrib import admin
from .models import PaymentTransaction, PaymentGatewayLog, Wallet, WalletTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'amount', 'status', 'payment_method', 'sender_phone', 'invoice_number', 'transaction_time', 'related_contribution')
    list_filter = ('status', 'payment_method', 'transaction_time', 'created_at')
    search_fields = ('transaction_id', 'sender_phone', 'invoice_number', 'related_contribution__member__user__username')
    raw_id_fields = ('related_contribution', 'processed_by') # For easier selection of related objects

@admin.register(PaymentGatewayLog)
class PaymentGatewayLogAdmin(admin.ModelAdmin):
    list_display = ('gateway_name', 'log_time', 'is_processed', 'related_transaction')
    list_filter = ('gateway_name', 'is_processed', 'log_time')
    search_fields = ('payload',) # Searching JSONField content
    raw_id_fields = ('related_transaction',)

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('member', 'balance', 'updated_at')
    search_fields = ('member__user__username',)

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'timestamp', 'description')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('wallet__member__user__username', 'description')
    raw_id_fields = ('wallet',)
