from django.db import models
from decimal import Decimal
from accounts.models import User # Import User model

class SaccoConfiguration(models.Model):
    current_financial_year_start = models.DateField(null=True, blank=True)
    current_financial_year_end = models.DateField(null=True, blank=True)
    max_loan_to_share_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=3.00, help_text="Maximum loan amount as a multiple of shares")
    min_credit_score_for_loan = models.IntegerField(default=550, help_text="Minimum credit score required for loan approval")
    target_member_growth = models.DecimalField(max_digits=5, decimal_places=2, default=0.10, help_text="Target annual member growth rate (e.g., 0.10 for 10%)")
    target_loan_portfolio_growth = models.DecimalField(max_digits=5, decimal_places=2, default=0.15, help_text="Target annual loan portfolio growth rate (e.g., 0.15 for 15%)")

    def save(self, *args, **kwargs):
        self.pk = 1 # Ensure only one instance exists
        super().save(*args, **kwargs)

    def __str__(self):
        return "SACCO System Configuration"

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action_time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    object_id = models.CharField(max_length=255, blank=True, null=True) # Can be UUID or PK

    class Meta:
        ordering = ['-action_time']

    def __str__(self):
        return f"{self.action_time}: {self.user.username if self.user else 'System'} - {self.action}"
