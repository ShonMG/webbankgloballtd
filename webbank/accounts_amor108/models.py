from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from pools.models import Pool
from decimal import Decimal # Import Decimal for precision

# Define constants for financial limits
GUARANTEE_EXPOSURE_LIMIT = Decimal('50000.00') # Example limit: Ksh 50,000
RISK_EXPOSURE_BREACH_LIMIT = Decimal('100000.00') # Example limit: Ksh 100,000

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

    # Pool Eligibility and Status Fields
    has_clean_contribution_history = models.BooleanField(default=True)
    outstanding_penalties_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    has_loan_arrears = models.BooleanField(default=False)
    guarantee_exposure_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    voting_rights_revoked = models.BooleanField(default=False)
    loan_visibility_reduced = models.BooleanField(default=False)
    reduced_credit_power = models.BooleanField(default=False)
    has_missed_contributions = models.BooleanField(default=False) # For downgrade trigger simulation

    # Next of Kin Information
    next_of_kin_names = models.CharField(max_length=255, blank=True)
    next_of_kin_mobile_no = models.CharField(max_length=15, blank=True)
    next_of_kin_email_address = models.EmailField(blank=True)
    next_of_kin_identification_passport_no = models.CharField(max_length=50, blank=True)
    next_of_kin_nationality = models.CharField(max_length=50, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def check_pool_entry_eligibility(self):
        """
        Checks if the member is eligible to join or upgrade a pool.
        Returns (True, "Eligible") if eligible, otherwise (False, "Reason for ineligibility").
        """
        if not self.has_clean_contribution_history:
            return False, "Contribution history is not clean."
        if self.outstanding_penalties_amount > 0:
            return False, f"Outstanding penalties: Ksh {self.outstanding_penalties_amount}"
        if self.has_loan_arrears:
            return False, "Has loan arrears."
        if self.guarantee_exposure_amount > GUARANTEE_EXPOSURE_LIMIT:
             return False, f"Guarantee exposure (Ksh {self.guarantee_exposure_amount}) exceeds limit (Ksh {GUARANTEE_EXPOSURE_LIMIT})."
        return True, "Eligible"

    def apply_downgrade_consequences(self):
        """
        Applies consequences of a pool downgrade.
        """
        self.loan_visibility_reduced = True
        self.voting_rights_revoked = True
        self.reduced_credit_power = True
        self.save()

    def check_and_apply_downgrade(self):
        """
        Checks for downgrade conditions and applies consequences if met.
        This method simulates the triggering mechanism.
        """
        downgrade_triggered = False
        reasons = []

        if self.has_missed_contributions:
            downgrade_triggered = True
            reasons.append("Missed contributions")
        if self.outstanding_penalties_amount > 0: # Any penalty triggers downgrade
            downgrade_triggered = True
            reasons.append(f"Penalty accumulation (Ksh {self.outstanding_penalties_amount})")
        if self.guarantee_exposure_amount > RISK_EXPOSURE_BREACH_LIMIT:
            downgrade_triggered = True
            reasons.append(f"Risk exposure breach (Ksh {self.guarantee_exposure_amount} > Ksh {RISK_EXPOSURE_BREACH_LIMIT})")

        if downgrade_triggered:
            self.apply_downgrade_consequences()
            # Optionally, log the downgrade and reasons
            print(f"User {self.user.username} downgraded due to: {', '.join(reasons)}")
            return True, reasons
        return False, []

class LoginHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"