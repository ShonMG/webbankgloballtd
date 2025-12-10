from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from accounts.models import User # Import the custom User model
from loans.models import LoanType
from shares.models import ShareConfig
from admin_panel.models import SaccoConfiguration
from notifications.models import NotificationSetting, NotificationTemplate # Import new models

class LoanTypeForm(forms.ModelForm):
    class Meta:
        model = LoanType
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'eligibility_criteria': forms.Textarea(attrs={'rows': 3}),
        }

class ShareConfigForm(forms.ModelForm):
    class Meta:
        model = ShareConfig
        fields = '__all__'

class SaccoConfigurationForm(forms.ModelForm):
    class Meta:
        model = SaccoConfiguration
        fields = '__all__'
        widgets = {
            'max_loan_to_share_ratio': forms.NumberInput(attrs={'step': '0.01'}),
            'target_member_growth': forms.NumberInput(attrs={'step': '0.01'}),
            'target_loan_portfolio_growth': forms.NumberInput(attrs={'step': '0.01'}),
        }

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'user_type', 'is_active', 'is_staff', 'is_superuser', 'phone_number', 'address', 'id_number', 'date_of_birth', 'member_id', 'date_joined_sacco', 'credit_score', 'is_verified')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_joined_sacco': forms.DateInput(attrs={'type': 'date'}),
        }

class NotificationSettingForm(forms.ModelForm):
    class Meta:
        model = NotificationSetting
        fields = '__all__'

class NotificationTemplateForm(forms.ModelForm):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        widgets = {
            'email_message_template': forms.Textarea(attrs={'rows': 5}),
            'sms_message_template': forms.Textarea(attrs={'rows': 3}),
        }
