from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Enter your email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Enter your password'})
    )

class SignUpForm(forms.ModelForm): # Inherit from forms.ModelForm
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=150, required=True, label="Last Name")
    phone_number = forms.CharField(max_length=15, required=True, label="Phone Number")
    email = forms.EmailField(label="Email", max_length=254, required=True)

    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'email', 'password', 'password2',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Assuming 'username' is not directly part of the form fields when inheriting from ModelForm
        # if 'username' in self.fields:
        #     del self.fields['username'] # This line is likely not needed anymore

        placeholders = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Enter your email',
            'phone_number': 'Enter your phone number',
            'password': 'Enter your password',
            'password2': 'Confirm your password',
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control form-control-lg'})
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and password2 and password != password2:
            self.add_error('password2', "Passwords don't match.")
        
        # Ensure email is used as username for the User model instance
        if 'email' in cleaned_data:
            cleaned_data['username'] = cleaned_data['email']

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Ensure username and email are set from the cleaned data
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'id_number', 'date_of_birth', 'profile_picture', 'preferred_director')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class UserSettingsForm(forms.ModelForm):
    # Profile Information (already there)
    # Security & Privacy
    profile_visibility = forms.ChoiceField(
        choices=User.PROFILE_VISIBILITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select w-auto'})
    )
    two_factor_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # Notification Preferences
    email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    sms_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    loan_status_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    payment_reminders = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    share_dividend_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    system_maintenance_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # Appearance & Language
    preferred_language = forms.ChoiceField(
        choices=User.PREFERRED_LANGUAGE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    preferred_currency = forms.ChoiceField(
        choices=User.PREFERRED_CURRENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    dark_mode_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'phone_number', 'address',
            'profile_visibility', 'two_factor_enabled',
            'email_notifications', 'sms_notifications',
            'loan_status_notifications', 'payment_reminders',
            'share_dividend_notifications', 'system_maintenance_notifications',
            'preferred_language', 'preferred_currency', 'dark_mode_enabled',
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply form-control to specific fields not covered by custom widgets above
        for field_name in ['first_name', 'last_name', 'email', 'phone_number', 'address']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})

        # Update attrs for checkbox fields to match template's fs-5 switch
        for field_name in ['two_factor_enabled', 'email_notifications', 'sms_notifications',
                           'loan_status_notifications', 'payment_reminders',
                           'share_dividend_notifications', 'system_maintenance_notifications',
                           'dark_mode_enabled']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'form-check-input fs-5'})