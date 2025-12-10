
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    USER_TYPES = (
        ('member', 'Member'),
        ('director', 'Director'),
        ('admin', 'System Admin'),
        ('guarantor', 'Guarantor'),
        ('founder', 'Founder'),
    )
    
    email = models.EmailField(unique=True) # Redefine email to make it unique
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='member')
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    id_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    member_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    date_joined_sacco = models.DateField(null=True, blank=True)
    credit_score = models.IntegerField(default=750)
    is_verified = models.BooleanField(default=False)
    preferred_director = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_members',
        limit_choices_to={'user_type': 'director'} # Filter choices to directors only
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"