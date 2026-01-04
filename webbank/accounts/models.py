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
    residential_area = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    id_number = models.CharField(max_length=20, blank=True)
    passport_no = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    member_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    date_joined_sacco = models.DateField(null=True, blank=True)
    credit_score = models.IntegerField(default=750)
    is_verified = models.BooleanField(default=False)

    # User Settings Fields
    PROFILE_VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
        ('only_me', 'Only Me'),
    ]
    profile_visibility = models.CharField(max_length=10, choices=PROFILE_VISIBILITY_CHOICES, default='private')
    two_factor_enabled = models.BooleanField(default=False) # Controls user preference for 2FA; full 2FA enforcement logic to be implemented separately.
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    loan_status_notifications = models.BooleanField(default=True)
    payment_reminders = models.BooleanField(default=True)
    share_dividend_notifications = models.BooleanField(default=True)
    system_maintenance_notifications = models.BooleanField(default=False)

    PREFERRED_LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
    ]
    preferred_language = models.CharField(max_length=5, choices=PREFERRED_LANGUAGE_CHOICES, default='en')

    PREFERRED_CURRENCY_CHOICES = [
        ('KES', 'KES (Ksh)'),
        ('USD', 'USD ($)'),
        ('EUR', 'EUR (€)'),
    ]
    preferred_currency = models.CharField(max_length=5, choices=PREFERRED_CURRENCY_CHOICES, default='KES')
    dark_mode_enabled = models.BooleanField(default=False)
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

class Testimonial(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimonials')
    quote = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial by {self.member.get_full_name() or self.member.username}"