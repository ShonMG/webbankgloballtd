from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from accounts.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('loan_approved', 'Loan Approved'),
        ('loan_rejected', 'Loan Rejected'),
        ('share_purchase', 'Share Purchase'),
        ('payment_due', 'Payment Due'),
        ('guarantee_request', 'Guarantee Request'),
        ('loan_pending_manager', 'Loan Pending Manager Review'),
        ('loan_manager_approved', 'Loan Approved by Manager'),
        ('loan_manager_rejected', 'Loan Rejected by Manager'),
        ('loan_pending_director', 'Loan Pending Director Review'),
        ('loan_director_approved', 'Loan Approved by Director'),
        ('loan_director_rejected', 'Loan Rejected by Director'),
        ('loan_fully_approved', 'Loan Fully Approved'),
        ('new_message', 'New Message'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Generic relation for related objects
    related_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('related_content_type', 'related_object_id')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class NotificationSetting(models.Model):
    enable_email_notifications = models.BooleanField(default=True)
    enable_sms_notifications = models.BooleanField(default=False)
    # Add other global settings here

    def save(self, *args, **kwargs):
        self.pk = 1 # Ensure only one instance exists
        super().save(*args, **kwargs)

    def __str__(self):
        return "Global Notification Settings"

class NotificationTemplate(models.Model):
    NOTIFICATION_TYPES_CHOICES = Notification.NOTIFICATION_TYPES

    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES_CHOICES, unique=True)
    subject_template = models.CharField(max_length=255, blank=True)
    email_message_template = models.TextField(blank=True)
    sms_message_template = models.TextField(blank=True)

    def __str__(self):
        return f"Template for {self.get_notification_type_display()}"