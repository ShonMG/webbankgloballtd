# webbankboard/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from members_amor108.models import Member as Amor108Member
from .models import WebBankMembership
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=Amor108Member)
def check_webbank_eligibility_on_pool_change(sender, instance, created, **kwargs):
    # This signal will be triggered whenever an Amor108Member is saved.
    # We only care if the 'pool' field has changed for an existing instance,
    # and if that change affects WebBank eligibility.

    if not created: # Only for existing instances being updated
        # To check if 'pool' actually changed, we need the old instance.
        # This is tricky with post_save. A common pattern is to store old values
        # in a pre_save signal, or re-fetch for simpler checks like this.
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return # Should not happen, but for safety

        # Check if the pool has actually changed
        if old_instance.pool != instance.pool:
            user = instance.user # Get the associated user

            # Check if this user is an active WebBank member
            webbank_membership = WebBankMembership.objects.filter(
                user=user,
                status=WebBankMembership.StatusChoices.ACTIVE
            ).first()

            if webbank_membership:
                # If they were a WebBank member, check their new AMOR108 pool status
                if not (instance.pool and instance.pool.name.upper() == 'GOLD'):
                    # User's AMOR108 pool is no longer GOLD, revoke WebBank membership
                    webbank_membership.status = WebBankMembership.StatusChoices.PENDING # Or EXITED, depending on policy
                    webbank_membership.save(update_fields=['status'])
                    # You might want to log this or send a notification to the user/admin
                    print(f"WebBank membership for {user.email} changed to PENDING due to AMOR108 pool downgrade.")
