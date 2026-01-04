from django.db import models
from django.conf import settings
from django.db.models import F # Import F object for atomic updates
from django.utils import timezone # Import timezone for deadline checks

class Resolution(models.Model):
    """
    Represents a governance resolution proposed within the system.
    """
    VOTE_TYPE_CHOICES = (
        ('ADVISORY', 'Advisory'),
        ('BINDING', 'Binding'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    visible_to_all = models.BooleanField(default=True)
    votable_by_gold_only = models.BooleanField(default=False, help_text="Only members of Gold tier pools can vote.")
    vote_type = models.CharField(max_length=10, choices=VOTE_TYPE_CHOICES, default='BINDING') # New field
    deadline = models.DateTimeField(null=True, blank=True, help_text="Date and time when voting closes.") # New field
    is_active = models.BooleanField(default=True, help_text="Is this resolution currently open for voting?") # New field
    
    creation_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_resolutions'
    )
    pool = models.ForeignKey(
        'pools.Pool', # Reference Pool model in the pools app
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolutions',
        help_text="The pool this resolution is specific to, if any."
    )
    # Fields to track votes directly on the resolution for quick access
    yes_votes = models.PositiveIntegerField(default=0)
    no_votes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def is_voting_open(self):
        return self.is_active and (self.deadline is None or self.deadline > timezone.now())

    def can_user_vote(self, user):
        """
        Checks if a user is eligible to vote on this resolution.
        """
        if not user.is_authenticated:
            return False, "User not authenticated."
        if not self.is_voting_open():
            return False, "Voting is not currently open for this resolution."

        # Assuming user has an amor108_profile
        if not hasattr(user, 'amor108_profile') or not user.amor108_profile.membership_pool:
            return False, "User is not part of any pool, or profile is incomplete."

        if self.votable_by_gold_only:
            # Assuming 'Gold' is a pool name indicating the highest tier
            if user.amor108_profile.membership_pool.name != 'Gold Tier': # Using 'Gold Tier' as per seed script
                return False, "Only Gold Tier members can vote on this resolution."
        
        # Check if user has already voted
        if self.votes.filter(voter=user).exists():
            return False, "You have already voted on this resolution."
            
        return True, "Eligible to vote."

    def record_vote(self, user, vote_choice):
        """
        Records a user's vote for this resolution.
        vote_choice: True for 'yes', False for 'no'.
        Returns (True, "Vote recorded") on success, (False, "Reason") on failure.
        """
        can_vote, reason = self.can_user_vote(user)
        if not can_vote:
            return False, reason
        
        # Record the vote
        Vote.objects.create(resolution=self, voter=user, vote_choice=vote_choice)

        # Update vote counts on the resolution
        if vote_choice:
            self.yes_votes = F('yes_votes') + 1
        else:
            self.no_votes = F('no_votes') + 1
        self.save(update_fields=['yes_votes', 'no_votes'])
        
        return True, "Vote recorded successfully."

    @property
    def total_votes(self):
        return self.yes_votes + self.no_votes
        
    @property
    def outcome(self):
        if self.is_voting_open():
            return 'Pending'
        if self.yes_votes > self.no_votes:
            return 'Passed'
        elif self.no_votes > self.yes_votes:
            return 'Failed'
        else:
            return 'Tied'

class Vote(models.Model):
    """
    Records a user's vote on a specific resolution.
    """
    resolution = models.ForeignKey(Resolution, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resolution_votes')
    vote_choice = models.BooleanField(help_text="True for 'Yes', False for 'No'")
    vote_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('resolution', 'voter') # A user can only vote once per resolution
        ordering = ['-vote_date']

    def __str__(self):
        return f"{self.voter.username} voted {'Yes' if self.vote_choice else 'No'} on {self.resolution.title}"
