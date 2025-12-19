from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from amor108.models import Pool # Assuming Pool model is defined in amor108 app

class MembershipStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Membership Statuses'

    def __str__(self):
        return self.name

class Member(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='amor108_member')
    pool = models.ForeignKey('amor108.Pool', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey(MembershipStatus, on_delete=models.SET_NULL, null=True, blank=True)
    date_joined_pool = models.DateField(auto_now_add=True)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)


    class Meta:
        verbose_name = 'Amor108 Member'
        verbose_name_plural = 'Amor108 Members'

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.status})"

class ExitRequest(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    request_date = models.DateField(auto_now_add=True)
    effective_exit_date = models.DateField(null=True, blank=True) # 30-day notice
    reason = models.TextField()
    is_approved = models.BooleanField(default=False)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='exit_requests_processed')

    def __str__(self):
        return f"Exit request by {self.member.user.get_full_name()} ({self.request_date})"
