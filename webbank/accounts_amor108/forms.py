from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.db import transaction # Import transaction for atomicity
from django.forms import DateInput, RadioSelect

from .models import Amor108Profile, Role
from members_amor108.models import Member, MembershipStatus # Import new models
from pools.models import Pool # Import Pool model to use in form field

User = get_user_model()


# Custom ModelChoiceField to format the label
class PoolModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Dynamically generate the description based on the Pool instance
        if obj.name == 'GOLD' and obj.contribution_amount == 10000 and obj.contribution_frequency == 'monthly':
            return f"GOLD: 12 members contributing Ksh 10,000 per month."
        elif obj.name == 'FIRST CLASS' and obj.contribution_amount == 7500 and obj.contribution_frequency == 'monthly':
            return f"FIRST CLASS: 12 members contributing Ksh 7,500 per month."
        elif obj.name == 'FIRST CLASS' and obj.contribution_amount == 5000 and obj.contribution_frequency == 'monthly':
            return f"FIRST CLASS: 12 members contributing Ksh 5,000 per month."
        elif obj.name == 'MIDDLE CLASS' and obj.contribution_amount == 100 and obj.contribution_frequency == 'daily':
            return f"MIDDLE CLASS: 12 members contributing Ksh 100 per day per month."
        elif obj.name == 'MIDDLE CLASS' and obj.contribution_amount == 2500 and obj.contribution_frequency == 'monthly':
            return f"MIDDLE CLASS: 24 members contributing Ksh 2500 per month."
        elif obj.name == 'ECONOMIC CLASS' and obj.contribution_amount == 50 and obj.contribution_frequency == 'daily':
            return f"ECONOMIC CLASS: 132 members contributing Ksh 50 per day per month."
        elif obj.name == 'ECONOMIC CLASS' and obj.contribution_amount == 1000 and obj.contribution_frequency == 'monthly':
            return f"ECONOMIC CLASS: 48 members contributing Ksh 1000 per month."
        elif obj.name == 'ECONOMIC CLASS' and obj.contribution_amount == 500 and obj.contribution_frequency == 'monthly':
            return f"ECONOMIC CLASS: 60 members contributing Ksh 500 per month."
        # Fallback if no specific description matches
        return f"{obj.name}: {obj.contribution_amount} {obj.contribution_frequency}"

class Amor108RegistrationForm(UserCreationForm):
    username = forms.CharField(widget=forms.HiddenInput(), required=False)
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}), label='Email Address')
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    residential_area = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mobile_no = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Mobile No')
    passport_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    nationality = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    id_or_passport_no = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='IDENTIFICATION CARD / PASSPORT NO')

    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    next_of_kin_names = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_mobile_no = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_email_address = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    next_of_kin_identification_passport_no = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_nationality = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    membership_pool = PoolModelChoiceField(
        queryset=Pool.objects.all(),
        widget=forms.RadioSelect,
        empty_label=None,
        required=False,
        label="Membership Pool"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'date_of_birth',
                  'residential_area', 'mobile_no', 'passport_photo', 'nationality',
                  'id_or_passport_no')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password2' in self.fields: # Remove password2 that UserCreationForm might add by default
            del self.fields['password2']

        for field_name, field in self.fields.items():
            if field_name not in ['membership_pool', 'passport_photo', 'password', 'password1']: # Exclude radio buttons, file input, and the newly defined password fields
                if hasattr(field.widget, 'attrs'):
                    current_class = field.widget.attrs.get('class', '')
                    if 'form-control' not in current_class:
                        field.widget.attrs['class'] = (current_class + ' form-control').strip()

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if email:
            cleaned_data['username'] = email

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password1")

        if password and password_confirm and password != password_confirm:
            self.add_error('password1', "Passwords don't match")
        
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get('email')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        user.residential_area = self.cleaned_data.get('residential_area')
        user.phone_number = self.cleaned_data.get('mobile_no')
        user.profile_picture = self.cleaned_data.get('passport_photo')
        user.nationality = self.cleaned_data.get('nationality')
        user.id_number = self.cleaned_data.get('id_or_passport_no')
        
        if commit:
            user.save()
            Amor108Profile.objects.create(
                user=user,
                role=self.cleaned_data.get('role'),
                is_approved=False,
                next_of_kin_names=self.cleaned_data.get('next_of_kin_names'),
                next_of_kin_mobile_no=self.cleaned_data.get('next_of_kin_mobile_no'),
                next_of_kin_email_address=self.cleaned_data.get('next_of_kin_email_address'),
                next_of_kin_identification_passport_no=self.cleaned_data.get('next_of_kin_identification_passport_no'),
                next_of_kin_nationality=self.cleaned_data.get('next_of_kin_nationality')
            )
            
            pending_status, created = MembershipStatus.objects.get_or_create(name='Pending Approval', defaults={'description': 'Member application submitted, awaiting admin review.'})
            Member.objects.create(
                user=user,
                pool=self.cleaned_data.get('membership_pool'),
                status=pending_status
            )
        return user

class Amor108AuthenticationForm(AuthenticationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'autofocus': True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email address'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )
        return cleaned_data

class Amor108ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    residential_area = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    nationality = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    id_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    passport_no = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    next_of_kin_names = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_mobile_no = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_email_address = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    next_of_kin_identification_passport_no = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_nationality = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'date_of_birth', 'residential_area',
            'phone_number', 'profile_picture', 'nationality', 'id_number', 'passport_no'
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and hasattr(self.instance, 'amor108_member'):
            member_instance = self.instance.amor108_member
            self.fields['next_of_kin_names'].initial = member_instance.next_of_kin_names
            self.fields['next_of_kin_mobile_no'].initial = member_instance.next_of_kin_mobile_no
            self.fields['next_of_kin_email_address'].initial = member_instance.next_of_kin_email_address
            self.fields['next_of_kin_identification_passport_no'].initial = member_instance.next_of_kin_identification_passport_no
            self.fields['next_of_kin_nationality'].initial = member_instance.next_of_kin_nationality
            
    def save(self, commit=True):
        user = super().save(commit=True)
        if hasattr(user, 'amor108_member'):
            member_instance = user.amor108_member
            member_instance.next_of_kin_names = self.cleaned_data.get('next_of_kin_names')
            member_instance.next_of_kin_mobile_no = self.cleaned_data.get('next_of_kin_mobile_no')
            member_instance.next_of_kin_email_address = self.cleaned_data.get('next_of_kin_email_address')
            member_instance.next_of_kin_identification_passport_no = self.cleaned_data.get('next_of_kin_identification_passport_no')
            member_instance.next_of_kin_nationality = self.cleaned_data.get('next_of_kin_nationality')
            member_instance.save()
        return user