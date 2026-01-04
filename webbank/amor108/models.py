from django.db import models
from django.conf import settings

class MembershipTier(models.Model):
    name = models.CharField(max_length=255)
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2)
    contribution_frequency = models.CharField(max_length=10, choices=[('daily', 'Daily'), ('monthly', 'Monthly')])

    def __str__(self):
        return self.name

class Contribution(models.Model):
    member = models.ForeignKey('members_amor108.Member', on_delete=models.CASCADE) # Link to members_amor108.Member
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.user.username} - {self.amount}"

class Loan(models.Model):
    LOAN_TYPE_CHOICES = [
        ('long_term', 'Long Term'),
        ('emergency', 'Emergency'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paid', 'Paid'),
    ]
    member = models.ForeignKey('members_amor108.Member', on_delete=models.CASCADE, null=True, blank=True) # Link to members_amor108.Member
    non_member_name = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)

    def __str__(self):
        if self.member:
            return f"Loan for {self.member.user.username}"
        else:
            return f"Loan for {self.non_member_name}"