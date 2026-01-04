from django.db import models
from members_amor108.models import Member

class Investment(models.Model):
    INVESTMENT_STATUS_CHOICES = (
        ('active', 'Active'),
        ('matured', 'Matured'),
        ('sold', 'Sold'),
    )

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='investments')
    investment_type = models.CharField(max_length=100, help_text="e.g., 'Stocks', 'Bonds', 'Real Estate'")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=INVESTMENT_STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.member.user.username}'s {self.investment_type} Investment"