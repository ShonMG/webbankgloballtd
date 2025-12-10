from django.db import models
from django.conf import settings

class Member(models.Model):
    MEMBER_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('REVIEW', 'Review'),
        ('INACTIVE', 'Inactive'),
    ]

    CONTACT_STATUS_CHOICES = [
        ('COMPLETE', 'Complete'),
        ('MISSING_PHONE', 'Missing Phone'),
        ('MISSING_EMAIL', 'Missing Email'),
        ('MISSING_INFO', 'Missing Info'),
    ]

    DATA_SOURCE_CHOICES = [
        ('CSV', 'CSV'),
        ('AMOR108', 'AMOR108'),
        ('MANUAL', 'Manual'),
    ]

    member_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    data_source = models.CharField(max_length=10, choices=DATA_SOURCE_CHOICES)
    status = models.CharField(max_length=10, choices=MEMBER_STATUS_CHOICES, default='PENDING')
    contact_status = models.CharField(max_length=20, choices=CONTACT_STATUS_CHOICES)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    monthly_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    shares = models.IntegerField(default=0)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    interest = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_members', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_members', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.member_id})"