from django import forms
from .models import Loan, LoanRepayment
from accounts.models import User # Import the User model

class LoanApplicationForm(forms.ModelForm):
    guarantors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(user_type='member'),
        required=False, # Guarantors might be optional
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        help_text="Select members who will guarantee this loan (optional)"
    )

    class Meta:
        model = Loan
        fields = ('loan_type', 'amount_applied', 'term_months', 'purpose', 'guarantors')
        widgets = {
            'loan_type': forms.Select(attrs={'class': 'form-control'}),
            'amount_applied': forms.NumberInput(attrs={'class': 'form-control'}),
            'term_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
        # Add any additional validation here if necessary, e.g., checking against loan balance
        return amount
