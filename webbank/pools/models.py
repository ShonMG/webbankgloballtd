from django.db import models
from django.conf import settings

class Pool(models.Model):
    """
    Represents an investment pool with specific contribution rules and member limits.
    """
    CONTRIBUTION_FREQUENCY_CHOICES = (
        ('DAILY', 'Daily'),
        ('MONTHLY', 'Monthly'),
    )

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2)
    contribution_frequency = models.CharField(max_length=10, choices=CONTRIBUTION_FREQUENCY_CHOICES)
    member_limit = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False, help_text="Automatically locked when member limit is reached.")
    creation_date = models.DateTimeField(auto_now_add=True)
    
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_pools',
        limit_choices_to={'user_type__in': ['director', 'admin', 'founder']},
        help_text="The user responsible for managing this pool."
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='pools',
        blank=True
    )

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()

    def check_and_lock_pool(self):
        if self.member_count >= self.member_limit:
            self.is_locked = True
        else:
            self.is_locked = False
        self.save()

class PoolManagerAssignment(models.Model):
    """
    Represents the assignment of a manager to a pool.
    """
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name='manager_assignments')
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pool_assignments',
        limit_choices_to={'user_type__in': ['director', 'admin', 'founder']}
    )
    assignment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('pool', 'manager')

    def __str__(self):
        return f"{self.manager.username} assigned to {self.pool.name}"