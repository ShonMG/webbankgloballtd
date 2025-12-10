from django import forms
from .models import Message, Conversation, MessageGroup
from accounts.models import User
from notifications.models import NotificationTemplate # Import NotificationTemplate

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': 'Subject (optional)'}),
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...'}),
        }

class ConversationForm(forms.Form):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select users to start a conversation with."
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your first message...'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Exclude the current user from the recipients list
            self.fields['recipients'].queryset = User.objects.exclude(id=user.id)

class MessageGroupForm(forms.ModelForm):
    class Meta:
        model = MessageGroup
        fields = ['name', 'description', 'members']
        widgets = {
            'members': forms.CheckboxSelectMultiple,
        }

class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = NotificationTemplate # Corrected from MessageTemplate
        fields = ['notification_type', 'subject_template', 'email_message_template', 'sms_message_template']
        widgets = {
            'email_message_template': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Email message template...'}),
            'sms_message_template': forms.Textarea(attrs={'rows': 3, 'placeholder': 'SMS message template...'}),
        }
