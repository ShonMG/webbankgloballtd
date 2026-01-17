from django.db import models
from django.conf import settings
from members_amor108.models import Member as Amor108Member
from loans.models import LoanRepayment
from decimal import Decimal

class ProfitCycle(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Calculation'),
        ('CALCULATED', 'Calculated'),
        ('DISTRIBUTED', 'Distributed'),
        ('CLOSED', 'Closed'),
    )

    name = models.CharField(max_length=100, unique=True, help_text="e.g., Q1 2025 Profit Distribution")
    start_date = models.DateField()
    end_date = models.DateField()
    total_profit_generated = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Total profit generated in this cycle from all sources.")
    total_distributed_profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Total profit distributed to members in this cycle.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    calculation_date = models.DateTimeField(auto_now_add=True)
    distributed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-end_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date}) - {self.get_status_display()}"

class MemberProfit(models.Model):
    ACTION_CHOICES = (
        ('PENDING', 'Pending Member Action'),
        ('WITHDRAWN', 'Withdrawn'),
        ('REINVESTED', 'Reinvested'),
        ('FORFEITED', 'Forfeited'), # If not acted upon within a period
    )

    profit_cycle = models.ForeignKey(ProfitCycle, on_delete=models.CASCADE, related_name='member_profits')
    member = models.ForeignKey(Amor108Member, on_delete=models.CASCADE, related_name='member_profits')
    
    allocated_profit = models.DecimalField(max_digits=12, decimal_places=2, help_text="Gross profit allocated to this member.")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, help_text="Net profit after tax.")
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='PENDING')
    action_date = models.DateTimeField(null=True, blank=True)
    
    # Optional: Link to a ShareTransaction if reinvested
    reinvestment_transaction = models.OneToOneField('shares.ShareTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='reinvested_profit')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('profit_cycle', 'member')
        ordering = ['-profit_cycle__end_date', 'member__user__username']

    def __str__(self):
        return f"{self.member.user.username} - {self.net_profit} ({self.get_action_display()}) in {self.profit_cycle.name}"

class InterestDistribution(models.Model):
    repayment = models.ForeignKey(LoanRepayment, on_delete=models.CASCADE, related_name='interest_distributions')
    member = models.ForeignKey(Amor108Member, on_delete=models.CASCADE, related_name='interest_earnings', null=True, blank=True)
    is_webbank_share = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.is_webbank_share:
            return f"Webbank share of {self.amount} from repayment {self.repayment.id}"
        return f"{self.member.user.username} earned {self.amount} from repayment {self.repayment.id}"
