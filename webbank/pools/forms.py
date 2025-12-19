from django import forms
from .models import Pool

class PoolForm(forms.ModelForm):
    class Meta:
        model = Pool
        fields = ['name', 'description', 'contribution_amount', 'contribution_frequency', 'member_limit']
