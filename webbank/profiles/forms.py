from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'residential_area',
            'mobile_no',
            'email_address',
            'passport_photo',
            'nationality',
            'identification_card_no',
            'passport_no',
            'kin_names',
            'kin_mobile_no',
            'kin_email_address',
            'kin_identification_passport_no',
            'kin_nationality',
        ]
