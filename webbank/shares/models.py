
# Create your models here.
from django.db import models
from accounts.models import User
from decimal import Decimal

class Share(models.Model):
    member = models.OneToOneField(User, on_delete=models.CASCADE, related_name='share')
    units = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monthly_share_target = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        null=True,
        blank=True,
        help_text="Target amount for monthly share contributions."
    )
    
    def save(self, *args, **kwargs):
        # Ensure both operands are Decimal before multiplication
        safe_units = Decimal(self.units if self.units is not None else 0)
        safe_unit_price = Decimal(self.unit_price if self.unit_price is not None else 0)
        self.total_value = safe_units * safe_unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.member.username} - {self.units} units"

class ShareTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('purchase', 'Share Purchase'),
        ('dividend', 'Dividend Payment'),
        ('bonus', 'Bonus Issue'),
    )
    
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='share_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    units = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    dividend = models.ForeignKey('Dividend', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    def __str__(self):
        return f"{self.transaction_type} - {self.member.username}"

class ShareConfig(models.Model):
    current_unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    dividend_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.05, help_text="Annual dividend rate (e.g., 0.05 for 5%)")
    dividend_frequency_months = models.IntegerField(default=12, help_text="How often dividends are paid in months")
    bonus_share_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0.01, help_text="Ratio of bonus shares per unit (e.g., 0.01 for 1 bonus share per 100 units)")
    bonus_min_units = models.IntegerField(default=100, help_text="Minimum units required to qualify for bonus shares")
    min_transfer_units = models.IntegerField(default=10, help_text="Minimum number of units that can be transferred")
    withdrawal_period_days = models.IntegerField(default=30, help_text="Number of days notice required for share withdrawal")
    dividend_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.05, help_text="Default tax rate on dividends (e.g., 0.05 for 5%)")

    def save(self, *args, **kwargs):
        self.pk = 1 # Ensure only one instance exists
        super().save(*args, **kwargs)

    def __str__(self):
        return "Share Configuration"

class Dividend(models.Model):
    declaration_date = models.DateField(auto_now_add=True)
    effective_date = models.DateField(help_text="Date from which shares are considered for this dividend")
    dividend_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Dividend rate for this declaration (e.g., 0.05 for 5%)")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.05, help_text="Tax rate applied to this dividend (e.g., 0.05 for 5%)")
    is_approved = models.BooleanField(default=False, help_text="Has this dividend declaration been approved for payment?")
    
    def __str__(self):
        return f"Dividend declared on {self.declaration_date} at {self.dividend_rate*100}%"
    
    class Meta:
        ordering = ['-declaration_date']