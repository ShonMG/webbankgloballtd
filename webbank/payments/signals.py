# webbank/payments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from loans.models import Loan
from .utils import disburse_loan
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Loan)
def handle_loan_disbursement(sender, instance, created, **kwargs):
    """
    Listens for a Loan being saved and triggers disbursement if the status is 'disbursed'.
    We check for disbursement_date to be None to prevent re-triggering.
    """
    if instance.status == 'disbursed':
        logger.debug(f"Signal received for loan {instance.loan_id} with status 'disbursed'.")
        # This check is important to prevent re-triggering if the loan is saved again.
        # The disburse_loan function itself is idempotent, but this avoids unnecessary function calls.
        if instance.disbursement_date is None:
            disburse_loan(instance)
