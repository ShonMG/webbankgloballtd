from django.db import models
from members_amor108.models import Member as Amor108Member

class ContributionStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Contribution(models.Model):
    member = models.ForeignKey(Amor108Member, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    status = models.ForeignKey(ContributionStatus, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.member.user.username} - {self.amount} on {self.date}"
