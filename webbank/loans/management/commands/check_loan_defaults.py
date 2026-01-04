from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan, LoanRepayment
from guarantees.models import Guarantee
from shares.models import ShareLock
from django.db import transaction
from decimal import Decimal
import logging
from audit.utils import log_admin_action
from accounts.models import User
from notifications.models import Notification

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks for overdue loan repayments and marks loans as defaulted if necessary.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        self.stdout.write(f"Starting default check for loans on {today}...")

        # Find all active loans
        active_loans = Loan.objects.filter(status='active').iterator()

        for loan in active_loans:
            overdue_repayments = LoanRepayment.objects.filter(
                loan=loan,
                due_date__lt=today, # Repayment due date is in the past
                status__in=['due'] # Status is still 'due' (not paid or already overdue)
            )

            if overdue_repayments.exists():
                # Mark these repayments as 'overdue'
                for repayment in overdue_repayments:
                    repayment.status = 'overdue'
                    repayment.save(update_fields=['status'])
                    logger.info(f"LoanRepayment {repayment.id} for Loan {loan.loan_id} marked as OVERDUE.")
                
                # Check if the loan itself should be marked as defaulted
                # A loan is defaulted if it has any overdue repayments
                if not loan.is_defaulted:
                    try:
                        with transaction.atomic():
                            loan.is_defaulted = True
                            loan.status = 'defaulted' # Change loan status to defaulted
                            loan.save(update_fields=['is_defaulted', 'status'])
                            self.stdout.write(self.style.WARNING(f"Loan {loan.loan_id} for {loan.amor108_member.user.username if loan.amor108_member else loan.member.username} has been marked as DEFAULTED."))
                            log_admin_action(None, 'LOAN_DEFAULTED', f"Loan {loan.loan_id} marked as defaulted due to overdue payments.", loan)

                            # Default Cascade Logic
                            active_guarantees = Guarantee.objects.filter(loan=loan, status='active')
                            for guarantee in active_guarantees:
                                self.stdout.write(self.style.WARNING(f"  -> Calling guarantee {guarantee.id} from {guarantee.guarantor.username}"))
                                guarantee.status = 'called'
                                guarantee.save(update_fields=['status'])
                                log_admin_action(None, 'GUARANTEE_CALLED', f"Guarantee {guarantee.id} for loan {loan.loan_id} called.", guarantee)
                                
                                try:
                                    share_lock = ShareLock.objects.get(guarantee=guarantee)
                                    share_account = share_lock.share_account
                                    
                                    # Liquidate shares
                                    share_account.units -= share_lock.locked_units
                                    share_account.save(update_fields=['units'])
                                    
                                    self.stdout.write(self.style.WARNING(f"    -> Liquidated {share_lock.locked_units} shares from {share_account.member.user.username}"))
                                    
                                    # Delete the lock
                                    share_lock.delete()

                                    # Notify Governance
                                    governance_users = User.objects.filter(user_type__in=['director', 'admin', 'founder'])
                                    for user in governance_users:
                                        Notification.objects.create(
                                            user=user,
                                            title='Loan Default and Guarantee Called',
                                            message=f"Loan {loan.loan_id} has defaulted. Guarantee {guarantee.id} from {guarantee.guarantor.username} has been called and shares liquidated.",
                                            notification_type='error',
                                            related_object=loan
                                        )
                                    self.stdout.write(self.style.SUCCESS(f"    -> Notified {governance_users.count()} governance members."))


                                except ShareLock.DoesNotExist:
                                    self.stdout.write(self.style.ERROR(f"  -> ERROR: ShareLock not found for guarantee {guarantee.id}"))
                                    # Decide if this should roll back the transaction
                                    pass

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"An error occurred while processing loan {loan.loan_id}: {e}"))

            else:
                # If there are no overdue repayments, ensure loan is not marked defaulted unnecessarily
                if loan.is_defaulted:
                    # This scenario might happen if a defaulted loan was manually rectified
                    # or if all overdue payments were eventually made.
                    # This logic assumes 'is_defaulted' should be False if no overdue repayments.
                    loan.is_defaulted = False
                    # Decide if status should revert from 'defaulted' to 'active'
                    # This depends on business rules. For now, if no overdue, set to 'active'.
                    if loan.status == 'defaulted':
                        loan.status = 'active'
                    loan.save(update_fields=['is_defaulted', 'status'])
                    self.stdout.write(self.style.SUCCESS(f"Loan {loan.loan_id} is no longer defaulted."))


        self.stdout.write(self.style.SUCCESS('Loan default check completed.'))
