from django.db import models
from django.conf import settings
from django.utils import timezone # For default timestamp
import uuid # For unique object_id if needed

class AuditLog(models.Model):
    """
    Records significant system events for auditing purposes.
    Logs are immutable once created.
    """
    ACTION_CHOICES = (
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('LOAN_APPLY', 'Loan Application'),
        ('LOAN_APPROVE', 'Loan Approval'),
        ('LOAN_REJECT', 'Loan Rejection'),
        ('LOAN_DISBURSE', 'Loan Disbursement'),
        ('LOAN_REPAY', 'Loan Repayment'),
        ('LOAN_DEFAULTED', 'Loan Defaulted'),
        ('GUARANTEE_CALLED', 'Guarantee Called'),
        ('CONTRIBUTION_MADE', 'Contribution Made'),
        ('CONTRIBUTION_VERIFIED', 'Contribution Verified'),
        ('PROFIT_WITHDRAWN', 'Profit Withdrawn'),
        ('PROFIT_REINVESTED', 'Profit Reinvested'),
        ('POOL_JOIN', 'Pool Joined'),
        ('POOL_UPGRADE', 'Pool Upgraded'),
        ('POOL_CREATE', 'Pool Created'),
        ('RESOLUTION_CREATE', 'Resolution Created'),
        ('RESOLUTION_VOTE', 'Resolution Voted'),
        ('MEMBER_REGISTER', 'Member Registration'),
        ('MEMBER_APPROVE', 'Member Approved'),
        ('RULE_CHANGE', 'System Rule Change'), # For governance/admin actions
        ('ADMIN_ACTION', 'Administrator Action'),
        ('PROFILE_UPDATE', 'Profile Update'),
        ('SHARE_PURCHASE', 'Share Purchase'),
        ('SHARE_TRANSFER', 'Share Transfer'),
        # Add more actions as the system grows
    )

    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, help_text="User who performed the action (or None for system actions).")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, editable=False)
    description = models.TextField(editable=False, help_text="Detailed description of the action.")
    model_name = models.CharField(max_length=100, blank=True, null=True, editable=False, help_text="Name of the model affected (e.g., 'Loan', 'Contribution').")
    object_id = models.CharField(max_length=36, blank=True, null=True, editable=False, help_text="PK of the object affected (e.g., UUID or int).") # Use CharField for flexibility (UUID/int)
    ip_address = models.GenericIPAddressField(blank=True, null=True, editable=False)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"[{self.timestamp}] {self.user} - {self.get_action_display()}: {self.description[:50]}..."
