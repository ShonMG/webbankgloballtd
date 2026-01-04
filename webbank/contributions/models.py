from django.db import models
from members_amor108.models import Member as Amor108Member

class ContributionStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Contribution(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('MPESA', 'M-Pesa'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other'),
    ]

    member = models.ForeignKey(Amor108Member, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    expected_date = models.DateField(null=True, blank=True) # New field to track when contribution was expected
    due_date = models.DateField(null=True, blank=True) # To track when the contribution was expected
    status = models.ForeignKey(ContributionStatus, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_code = models.CharField(max_length=100, blank=True, null=True, help_text="Transaction code from payment gateway")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='MPESA')
    is_verified = models.BooleanField(default=False, help_text="Indicates if the contribution has been verified.")

    def __str__(self):
        return f"{self.member.user.username} - {self.amount} on {self.date}"
