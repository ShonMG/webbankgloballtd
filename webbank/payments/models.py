from django.db import models
from django.conf import settings
from django.utils import timezone
from contributions.models import Contribution # Assuming contributions app has a Contribution model

class PaymentTransaction(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
        ('INITIATED', 'Initiated'), # For transactions initiated by the system (e.g., a payment request)
    )

    TRANSACTION_TYPE_CHOICES = (
        ('MPESA_PAYBILL', 'M-Pesa Paybill'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('OTHER', 'Other'),
    )

    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="Unique ID from payment gateway (e.g., M-Pesa 'KQG123XYZ')")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KSH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES, default='MPESA_PAYBILL')
    
    sender_phone = models.CharField(max_length=15, blank=True, null=True)
    sender_name = models.CharField(max_length=100, blank=True, null=True)

    # M-Pesa specific fields
    shortcode = models.CharField(max_length=20, blank=True, null=True, help_text="The Paybill or Till number")
    invoice_number = models.CharField(max_length=100, blank=True, null=True, help_text="Reference number from sender (e.g., account number)")
    
    transaction_time = models.DateTimeField(default=timezone.now)
    
    # Link to Contribution (for Amor108 payments)
    # This assumes a direct mapping to a Contribution. If there are other types of receivable items
    # a GenericForeignKey might be more appropriate.
    related_contribution = models.ForeignKey(Contribution, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transactions')

    # For manual overrides or system-initiated payments
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payments')
    notes = models.TextField(blank=True, help_text="Internal notes for reconciliation or manual actions.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_time']

    def __str__(self):
        return f"{self.transaction_id or 'N/A'} - {self.amount} {self.currency} - {self.status}"

class PaymentGatewayLog(models.Model):
    gateway_name = models.CharField(max_length=50, default='M-Pesa')
    log_time = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(help_text="Raw payload received from the payment gateway.")
    is_processed = models.BooleanField(default=False)
    
    # Link to the processed transaction
    related_transaction = models.OneToOneField(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='gateway_log')

    notes = models.TextField(blank=True, help_text="Any issues encountered during processing or manual review notes.")

    class Meta:
        ordering = ['-log_time']

    def __str__(self):
        return f"{self.gateway_name} Log - {self.log_time} - Processed: {self.is_processed}"
