import logging
from decimal import Decimal
from django.contrib.auth import get_user_model
from members_amor108.models import Member as Amor108Member
from payments.models import Wallet, WalletTransaction
from .models import InterestDistribution

logger = logging.getLogger(__name__)

def get_profit_summary(user):
    """
    Placeholder for profit summary logic.
    """
    logger.warning("Using placeholder get_profit_summary function.")
    return {
        'accrued_profits': Decimal('0.00'),
        'withdrawn_profits': Decimal('0.00'),
        'reinvested_profits': Decimal('0.00'),
        'pending_profits': [],
        'can_withdraw': False,
        'withdrawal_ineligibility_reasons': ['Profit features are currently under development.'],
    }

def distribute_interest(repayment):
    """
    Distributes the interest portion of a loan repayment to WebBank and members.
    """
    loan = repayment.loan
    loan_type = loan.loan_type
    interest_paid = repayment.interest_amount

    if interest_paid <= 0 or loan_type.interest_rate <= 0:
        logger.info(f"No interest to distribute for repayment {repayment.id}.")
        return

    # --- WebBank's Share ---
    if loan_type.webbank_interest_share > 0:
        webbank_share_amount = (interest_paid * (loan_type.webbank_interest_share / loan_type.interest_rate)).quantize(Decimal('0.01'))
        
        User = get_user_model()
        webbank_user, _ = User.objects.get_or_create(username='webbank', defaults={'is_staff': True, 'is_superuser': True})
        webbank_member, _ = Amor108Member.objects.get_or_create(user=webbank_user)
        webbank_wallet, _ = Wallet.objects.get_or_create(member=webbank_member)
        
        webbank_wallet.balance += webbank_share_amount
        webbank_wallet.save()

        InterestDistribution.objects.create(
            repayment=repayment,
            is_webbank_share=True,
            amount=webbank_share_amount
        )
        logger.info(f"Distributed {webbank_share_amount} to WebBank from repayment {repayment.id}.")

    # --- Members' Share ---
    if loan_type.member_interest_share > 0:
        total_member_share = (interest_paid * (loan_type.member_interest_share / loan_type.interest_rate)).quantize(Decimal('0.01'))
        
        active_members = Amor108Member.objects.filter(is_suspended=False).exclude(user__username='webbank')
        member_count = active_members.count()

        if member_count > 0:
            share_per_member = (total_member_share / member_count).quantize(Decimal('0.01'))
            
            # This can be slow for a large number of members.
            # In a production system, this should be an asynchronous background task.
            for member in active_members:
                member_wallet, _ = Wallet.objects.get_or_create(member=member)
                member_wallet.balance += share_per_member
                member_wallet.save()

                WalletTransaction.objects.create(
                    wallet=member_wallet,
                    transaction_type='FEE', # Using 'FEE' as a generic earning type
                    amount=share_per_member,
                    description=f"Interest share from loan {loan.loan_id}"
                )

                InterestDistribution.objects.create(
                    repayment=repayment,
                    member=member,
                    amount=share_per_member
                )
            
            logger.info(f"Distributed {total_member_share} among {member_count} members.")
        else:
            logger.warning("No active members found to distribute interest to.")
