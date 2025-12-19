from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan, LoanRepayment
from decimal import Decimal
import logging

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
                    loan.is_defaulted = True
                    loan.status = 'defaulted' # Change loan status to defaulted
                    loan.save(update_fields=['is_defaulted', 'status'])
                    self.stdout.write(self.style.WARNING(f"Loan {loan.loan_id} for {loan.amor108_member.user.username if loan.amor108_member else loan.member.username} has been marked as DEFAULTED."))
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
