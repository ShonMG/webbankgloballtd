from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    residential_area = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=20)
    email_address = models.EmailField()
    passport_photo = models.ImageField(upload_to='passport_photos/')
    nationality = models.CharField(max_length=100)
    identification_card_no = models.CharField(max_length=100, blank=True)
    passport_no = models.CharField(max_length=100, blank=True)
    
    # Next of Kin
    kin_names = models.CharField(max_length=255)
    kin_mobile_no = models.CharField(max_length=20)
    kin_email_address = models.EmailField()
    kin_identification_passport_no = models.CharField(max_length=100)
    kin_nationality = models.CharField(max_length=100)
    
    # Approval status
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'