from django import forms
from .models import Loan, LoanRepayment, LoanType
from members_amor108.models import Member as Amor108Member
from shares.models import Share
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Sum

class LoanApplicationForm(forms.ModelForm):
    guest_first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}), label="First Name")
    guest_last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}), label="Last Name")
    guest_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control form-control-lg'}), label="Email")

    guarantors = forms.ModelMultipleChoiceField(
        queryset=Amor108Member.objects.filter(
            status__name='Active',
            is_suspended=False,
            user__amor108_profile__is_approved=True
        ),
        required=False,
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
        self.user = kwargs.pop('user', None)
        is_guest_loan = kwargs.pop('is_guest_loan', False)
        super().__init__(*args, **kwargs)

        if is_guest_loan:
            self.fields['guest_first_name'].required = True
            self.fields['guest_last_name'].required = True
            self.fields['guest_email'].required = True
        else:
            if 'guest_first_name' in self.fields:
                del self.fields['guest_first_name']
            if 'guest_last_name' in self.fields:
                del self.fields['guest_last_name']
            if 'guest_email' in self.fields:
                del self.fields['guest_email']

    def clean(self):
        cleaned_data = super().clean()
        amount_applied = cleaned_data.get('amount_applied')
        guarantors = cleaned_data.get('guarantors')

        # LAW 7: Enforce Share-Based Credit Limit for members
        if self.user and self.user.is_authenticated and hasattr(self.user, 'amor108_member'):
            try:
                share_account = self.user.amor108_member.share_account
                total_shares_value = share_account.total_value
            except Share.DoesNotExist:
                total_shares_value = Decimal('0.00')

            outstanding_loans = Loan.objects.filter(
                amor108_member=self.user.amor108_member,
                status__in=['active', 'disbursed']
            ).aggregate(total=Sum('outstanding_principal'))['total'] or Decimal('0.00')

            max_loan_limit = total_shares_value * settings.LOAN_TO_SHARE_MULTIPLIER
            available_credit = max_loan_limit - outstanding_loans
            
            if amount_applied > available_credit:
                raise ValidationError(
                    f"Your loan application of KES {amount_applied:,.2f} exceeds your available credit limit of KES {available_credit:,.2f}. "
                    f"Your limit is based on your share value of KES {total_shares_value:,.2f}."
                )

        # LAW 8: Guarantor Risk Law
        if guarantors:
            total_guarantor_shares = Decimal('0.00')
            for guarantor in guarantors:
                try:
                    guarantor_share_value = guarantor.share_account.total_value
                    # A guarantor's shares are locked by their own loans
                    guarantor_outstanding_loans = Loan.objects.filter(
                        amor108_member=guarantor,
                        status__in=['active', 'disbursed']
                    ).aggregate(total=Sum('outstanding_principal'))['total'] or Decimal('0.00')
                    
                    available_guarantor_shares = guarantor_share_value - guarantor_outstanding_loans
                    total_guarantor_shares += max(Decimal('0.00'), available_guarantor_shares)

                except Share.DoesNotExist:
                    continue # This guarantor has no shares, so they can't contribute
            
            if total_guarantor_shares < amount_applied:
                raise ValidationError(
                    f"The selected guarantors do not have enough available shares (KES {total_guarantor_shares:,.2f}) to cover the requested loan amount of KES {amount_applied:,.2f}."
                )

        return cleaned_data


class Amor108LoanApplicationForm(forms.ModelForm):
    guarantors = forms.ModelMultipleChoiceField(
        queryset=Amor108Member.objects.filter(
            status__name='Active',
            is_suspended=False,
            user__amor108_profile__is_approved=True
        ),
        required=False,
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
        return amount


