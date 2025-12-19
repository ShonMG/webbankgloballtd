from django import forms
from .models import Loan, Contribution, Pool # Keep Pool import for PoolChoiceField

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['amount', 'loan_type']

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['amount']