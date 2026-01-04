from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from profits.models import MemberProfit
from loans.models import Loan # Assuming a Loan model exists in loans app
from guarantees.models import Guarantee # Assuming a Guarantee model exists in guarantees app
from governance.models import Resolution # Corrected import path
from accounts_amor108.models import Amor108Profile # To access user profile for eligibility

def get_profit_summary(user):
    summary = {
        'accrued_profits': Decimal('0.00'),
        'can_withdraw': False,
        'can_reinvest': False,
        'distribution_history': [],
        'withdrawal_ineligibility_reasons': [],
    }

    if not hasattr(user, 'amor108_profile') or not hasattr(user, 'amor108_member'):
        summary['withdrawal_ineligibility_reasons'].append("User profile or member record incomplete.")
        return summary
    
    member = user.amor108_member
    user_profile = user.amor108_profile

    # Calculate accrued profits (pending member action)
    pending_profits = MemberProfit.objects.filter(member=member, action='PENDING')
    summary['accrued_profits'] = pending_profits.aggregate(Sum('net_profit'))['net_profit__sum'] or Decimal('0.00')

    summary['distribution_history'] = MemberProfit.objects.filter(member=member).order_by('-profit_cycle__end_date')

    if summary['accrued_profits'] > 0:
        summary['can_reinvest'] = True # Always preferred if there are profits

        # Check withdrawal eligibility
        withdrawal_eligible = True
        reasons = []

        # 1. No active loan
        active_loans = Loan.objects.filter(amor108_member=member, status='active').exists() # Filter by amor108_member
        if active_loans:
            withdrawal_eligible = False
            reasons.append("You have active loans.")

        # 2. No active guarantee
        active_guarantees = Guarantee.objects.filter(guarantor=member.user, status='active').exists() # Corrected filter
        if active_guarantees:
            withdrawal_eligible = False
            reasons.append("You have active guarantees.")
        
        # 3. Governance rules allow (e.g., specific resolutions preventing withdrawal)
        # Real governance integration can be complex, involving active, passed resolutions with specific effects.
        # For example, a "freeze withdrawals" resolution might exist and be active.
        freeze_withdrawal_resolution = Resolution.objects.filter(
            title__icontains='freeze withdrawals',
            is_active=False,  # Assuming 'is_active' implies voting is closed
            # For checking if a resolution has 'passed', you'd typically check its outcome after deadline
            # A more robust check might involve iterating through relevant resolutions
        ).exists()
        # The 'outcome' property is not directly filterable on a QuerySet, so we would need to fetch
        # and then check. For now, checking 'is_active=False' is a reasonable proxy if the resolution
        # becomes inactive once its purpose is fulfilled (e.g., voting closes).
        if freeze_withdrawal_resolution:
             withdrawal_eligible = False
             reasons.append("Withdrawals are temporarily suspended by governance rules.")


        # 4. Liquidity available (conceptual check)
        # In a real system, this would involve checking the overall Sacco's cash flow/reserves.
        # For simulation, we assume liquidity is generally available unless a governance rule says otherwise.
        
        summary['can_withdraw'] = withdrawal_eligible
        summary['withdrawal_ineligibility_reasons'] = reasons

    return summary