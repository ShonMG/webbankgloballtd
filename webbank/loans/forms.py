from django import forms
from .models import Loan, LoanRepayment, LoanType
from members_amor108.models import Member as Amor108Member, MembershipStatus # Import Amor108Member and MembershipStatus
from django.core.exceptions import ValidationError
from django.db.models import Sum
from contributions.models import Contribution # Assuming Contribution model exists
from django.utils import timezone
from collections import defaultdict


class LoanApplicationForm(forms.ModelForm):
    guest_first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}), label="First Name")
    guest_last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}), label="Last Name")
    guest_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control form-control-lg'}), label="Email")

    guarantors = forms.ModelMultipleChoiceField(
        queryset=Amor108Member.objects.filter(
            status__name='Active', # Only active members can be guarantors
            is_suspended=False,
            user__amor108_profile__is_approved=True # Ensure their Amor108Profile is approved
        ),
        required=False, # Guarantors might be optional
        widget=forms.SelectMultiple(attrs={'class': 'form-control form-control-lg'}),
        help_text="Select members who will guarantee this loan"
    )

    class Meta:
        model = Loan
        fields = ('loan_type', 'amount_applied', 'term_months', 'purpose', 'guarantors', 'guest_first_name', 'guest_last_name', 'guest_email')
        widgets = {
            'loan_type': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'amount_applied': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'term_months': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) # Pop the user from kwargs
        super().__init__(*args, **kwargs)

        if not self.user or not self.user.is_authenticated:
            # If user is not authenticated, guest fields are required and guarantors are not applicable
            self.fields['guest_first_name'].required = True
            self.fields['guest_last_name'].required = True
            self.fields['guest_email'].required = True
            if 'guarantors' in self.fields: # Ensure field exists before trying to delete
                del self.fields['guarantors']
        else:
            # If user is authenticated, guest fields are not applicable
            if 'guest_first_name' in self.fields:
                del self.fields['guest_first_name']
            if 'guest_last_name' in self.fields:
                del self.fields['guest_email']
            if 'guest_email' in self.fields:
                del self.fields['guest_email']

class Amor108LoanApplicationForm(forms.ModelForm):
    guarantors = forms.ModelMultipleChoiceField(
        queryset=Amor108Member.objects.filter(
            status__name='Active', # Only active members can be guarantors
            is_suspended=False,
            user__amor108_profile__is_approved=True # Ensure their Amor108Profile is approved
        ),
        required=False, # Guarantors might be optional
        widget=forms.SelectMultiple(attrs={'class': 'form-control form-control-lg'}),
        help_text="Select members who will guarantee this loan (optional)"
    )

    class Meta:
        model = Loan
        fields = ('loan_type', 'amount_applied', 'term_months', 'purpose', 'guarantors')
        widgets = {
            'loan_type': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'amount_applied': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'term_months': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None) # Pop the user from kwargs
        super().__init__(*args, **kwargs)
        # Filter loan types that are specifically for Amor108 members, if applicable
        # Or exclude non-member loan types if the form is only for members
        self.fields['loan_type'].queryset = LoanType.objects.exclude(name='Non-member')

    def clean(self):
        cleaned_data = super().clean()
        loan_type = cleaned_data.get('loan_type')
        amount_applied = cleaned_data.get('amount_applied')
        term_months = cleaned_data.get('term_months')

        # Ensure user is an Amor108Member
        if not (self.request_user and hasattr(self.request_user, 'amor108_member')):
            raise ValidationError("You must be an Amor108 member to apply for this loan.")
            
        amor108_member = self.request_user.amor108_member
        
        # Block defaulters from new loans
        if Loan.objects.filter(amor108_member=amor108_member, is_defaulted=True).exists():
            raise ValidationError("You have defaulted on a previous loan and cannot apply for a new one.")
        
        # Eligibility based on contribution history (simplified example)
        required_active_months = 3
        min_total_contribution = Decimal('5000.00')

        active_contributions = Contribution.objects.filter(
            member=amor108_member.contributions.all(), # Assuming amor108_member.contributions is a reverse relation
            status__name='Paid',
            date__lte=timezone.now().date()
        ).order_by('date')

        monthly_contributions = defaultdict(Decimal)
        for contrib in active_contributions:
            month_key = contrib.date.strftime('%Y-%m')
            monthly_contributions[month_key] += contrib.amount
        
        if len(monthly_contributions) < required_active_months:
            raise ValidationError(f"You need at least {required_active_months} months of active contributions to apply for a loan.")
        
        total_contributed = sum(monthly_contributions.values())
        if total_contributed < min_total_contribution:
            raise ValidationError(f"You need a minimum total contribution of Ksh {min_total_contribution} to apply for a loan.")

        # Validate amount and term against loan type limits
        if loan_type:
            if amount_applied < loan_type.min_amount:
                raise ValidationError(f"Minimum amount for {loan_type.name} is Ksh {loan_type.min_amount}.")
            if amount_applied > loan_type.max_amount:
                raise ValidationError(f"Maximum amount for {loan_type.name} is Ksh {loan_type.max_amount}.")
            if term_months > loan_type.max_term_months:
                raise ValidationError(f"Maximum term for {loan_type.name} is {loan_type.max_term_months} months.")

        return cleaned_data


class LoanRepaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text="Enter the amount you wish to repay."
    )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        # Add any additional validation here if necessary, e.g., checking against loan balance
        return amount

