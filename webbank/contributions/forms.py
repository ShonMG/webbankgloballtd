from django import forms
from .models import Contribution

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['amount', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
