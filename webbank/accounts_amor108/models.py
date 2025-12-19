from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from pools.models import Pool

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.name

class PermissionProfile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.name

class Amor108Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='amor108_profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    membership_pool = models.ForeignKey(Pool, on_delete=models.SET_NULL, null=True, blank=True, related_name='amor108_profiles')

    # Next of Kin Information
    next_of_kin_names = models.CharField(max_length=255, blank=True)
    next_of_kin_mobile_no = models.CharField(max_length=15, blank=True)
    next_of_kin_email_address = models.EmailField(blank=True)
    next_of_kin_identification_passport_no = models.CharField(max_length=50, blank=True)
    next_of_kin_nationality = models.CharField(max_length=50, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class LoginHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"