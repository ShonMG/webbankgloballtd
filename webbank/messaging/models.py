from django.db import models
from django.conf import settings
from accounts.models import User # Assuming User model is in accounts app

class Conversation(models.Model):
    """
    Represents a conversation thread between users.
    """
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id}"

class Message(models.Model):
    """
    Represents an individual message within a conversation or a broadcast.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    
    # Recipients for broadcast messages or when a message is not part of a conversation
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='received_broadcast_messages', blank=True)
    
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_messages', blank=True)
    is_broadcast = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Message from {self.sender} - {self.subject or self.body[:50]}"

class MessageTemplate(models.Model):
    """
    Stores predefined message templates.
    """
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class MessageGroup(models.Model):
    """
    Defines groups of users for broadcasting messages.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='message_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
