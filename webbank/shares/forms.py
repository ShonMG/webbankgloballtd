from django import forms
from .models import Share, Dividend

class SharePurchaseForm(forms.Form):
    units = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of units to purchase'})
    )

class ShareGoalForm(forms.ModelForm):
    class Meta:
        model = Share
        fields = ['monthly_share_target']
        widgets = {
            'monthly_share_target': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter your monthly share target'})
        }

class DividendForm(forms.ModelForm):
    class Meta:
        model = Dividend
        fields = ['effective_date', 'dividend_rate', 'tax_rate']
        widgets = {
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'dividend_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g., 0.05 for 5%'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g., 0.10 for 10%'}),
        }
        labels = {
            'effective_date': 'Effective Date',
        }

