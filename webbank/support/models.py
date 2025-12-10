from django.db import models
from accounts.models import User

class SupportTicket(models.Model):
    TICKET_CATEGORIES = (
        ('account_issues', 'Account Issues'),
        ('loans', 'Loans'),
        ('shares', 'Shares'),
        ('technical', 'Technical Support'),
        ('general', 'General Inquiry'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    ticket_id = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=TICKET_CATEGORIES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"