from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.db import transaction # Import transaction for atomicity
from django.forms import DateInput, RadioSelect

from .models import Amor108Profile, Role
from members_amor108.models import Member, MembershipStatus # Import new models
from amor108.models import Pool # Import Pool model to use in form field

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
    # User Model Fields
    # The username field is provided by UserCreationForm, so we don't redefine it here.
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email_address = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}), label='Email Address')
    date_of_birth = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    residential_area = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mobile_no = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Mobile No')
    passport_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    nationality = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    identification_card_no = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Identification Card No')
    passport_no = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Amor108Profile Fields
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    next_of_kin_names = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_mobile_no = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_email_address = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    next_of_kin_identification_passport_no = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_nationality = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    membership_pool = PoolModelChoiceField(
        queryset=Pool.objects.all(),
        widget=forms.RadioSelect, # As per template
        empty_label=None,
        required=False,
        label="Membership Pool"
    )


    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email_address', 'date_of_birth',
                  'residential_area', 'mobile_no', 'passport_photo', 'nationality',
                  'identification_card_no', 'passport_no', 'role', 'next_of_kin_names',
                  'next_of_kin_mobile_no', 'next_of_kin_email_address',
                  'next_of_kin_identification_passport_no', 'next_of_kin_nationality',
                  'membership_pool')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply form-control class to all fields automatically for better styling
        for field_name, field in self.fields.items():
            if field_name not in ['membership_pool', 'passport_photo', 'password', 'password2']: # Exclude radio buttons, file input, and password fields
                if hasattr(field.widget, 'attrs'):
                    field.widget.attrs['class'] = 'form-control'
            
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email_address')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        user.residential_area = self.cleaned_data.get('residential_area')
        user.phone_number = self.cleaned_data.get('mobile_no')
        user.profile_picture = self.cleaned_data.get('passport_photo')
        user.nationality = self.cleaned_data.get('nationality')
        user.id_number = self.cleaned_data.get('identification_card_no')
        user.passport_no = self.cleaned_data.get('passport_no')
        
        if commit:
            user.save()
            # Create Amor108Profile (retains role and is_approved)
            Amor108Profile.objects.create(
                user=user,
                role=self.cleaned_data.get('role'),
                is_approved=False # Default to not approved on signup
            )
            
            # Create members_amor108.Member instance
            pending_status, created = MembershipStatus.objects.get_or_create(name='Pending Approval', defaults={'description': 'Member application submitted, awaiting admin review.'})
            Member.objects.create(
                user=user,
                pool=self.cleaned_data.get('membership_pool'),
                status=pending_status,
                next_of_kin_names=self.cleaned_data.get('next_of_kin_names'),
                next_of_kin_mobile_no=self.cleaned_data.get('next_of_kin_mobile_no'),
                next_of_kin_email_address=self.cleaned_data.get('next_of_kin_email_address'),
                next_of_kin_identification_passport_no=self.cleaned_data.get('next_of_kin_identification_passport_no'),
                next_of_kin_nationality=self.cleaned_data.get('next_of_kin_nationality')
            )
        return user

class Amor108AuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })

    class Meta:
        model = User
        fields = ['username', 'password']
