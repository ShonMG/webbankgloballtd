from django import forms
from django.utils.crypto import get_random_string
from .models import Loan, Contribution, Pool, Member
from accounts.models import User # Assuming User model is in accounts app

class Amor108RegistrationForm(forms.ModelForm):
    # Personal Information
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    residential_area = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mobile_no = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email_address = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    passport_photo = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'})) # Assuming ImageField for passport photo
    nationality = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    identification_card_no = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    passport_no = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Next of Kin Information
    next_of_kin_names = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_mobile_no = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_email_address = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    next_of_kin_identification_passport_no = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_of_kin_nationality = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Membership Type (Radio select for pools)
    membership_pool = forms.ModelChoiceField(
        queryset=Pool.objects.all(),
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        empty_label=None,
        label="Select Membership Pool"
    )

    class Meta:
        model = Member
        fields = []

    def save(self, commit=True):
        # Create a new User object
        user = User.objects.create_user(
            username=self.cleaned_data['email_address'], # Using email as username for simplicity
            email=self.cleaned_data['email_address'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=get_random_string(12)
        )
        user.is_active = False # Deactivate account until approval
        user.user_type = 'member' # Assigning 'member' user type
        user.save()

        # Create a Member object linked to the new User and selected Pool
        member = super().save(commit=False)
        member.user = user
        member.pool = self.cleaned_data['membership_pool']
        member.status = 'pending'
        # Assign other fields from the form to the member or a new profile model
        # For now, we are just creating the user and member, additional profile fields will be handled later
        if commit:
            member.save()
        return member


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['amount', 'loan_type']

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['amount']

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
