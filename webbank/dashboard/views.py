from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from shares.models import Share
from loans.models import Loan
from shares.models import ShareTransaction
from decimal import Decimal
from webbankboard.models import WebBankMembership
from django.conf import settings

@login_required
def main_dashboard(request):
    user = request.user
    
    # Redirect admin and founder to their specific dashboards
    if user.user_type in ['admin', 'founder']:
        if user.user_type == 'admin':
            return redirect('admin_panel:admin_dashboard')
        else:
            return redirect('admin_panel:founder_dashboard')
    
    is_amor108_member = hasattr(user, 'amor108_member')
    is_webbank_member = False
    
    total_shares = Decimal('0.00')
    active_loans_count = 0
    outstanding_loan_amount = Decimal('0.00')
    recent_transactions = []
    active_user_loans = []

    if is_amor108_member:
        # All members (including WebBank members) are AMOR108 members first.
        # So we always start with AMOR108 data.
        amor108_member_instance = user.amor108_member
        
        try:
            # Shares are only for AMOR108 members
            total_shares = amor108_member_instance.share_account.total_value
        except (Share.DoesNotExist, AttributeError): # Added AttributeError for safety
            total_shares = Decimal('0.00')
            
        # A user can have loans as an AMOR108 member
        active_loans_count = Loan.objects.filter(amor108_member=amor108_member_instance, status__in=['active', 'disbursed']).count()
        outstanding_loan_amount = Loan.objects.filter(
            amor108_member=amor108_member_instance, 
            status__in=['active', 'disbursed']
        ).aggregate(total=Sum('amount_approved'))['total'] or Decimal('0.00')
        
        recent_transactions = ShareTransaction.objects.filter(member=amor108_member_instance).order_by('-transaction_date')[:5]
        active_user_loans = list(Loan.objects.filter(amor108_member=amor108_member_instance, status__in=['active', 'disbursed']))

        # Now, check for WebBank status and add WebBank-specific data
        if WebBankMembership.objects.filter(user=user, status=WebBankMembership.StatusChoices.ACTIVE).exists():
            is_webbank_member = True
            # WebBank members can also take loans as a User
            webbank_loans = Loan.objects.filter(member=user, status__in=['active', 'disbursed'])
            active_loans_count += webbank_loans.count()
            outstanding_loan_amount += webbank_loans.aggregate(total=Sum('amount_approved'))['total'] or Decimal('0.00')
            active_user_loans.extend(list(webbank_loans))

    # Eligibility for WebBank
    is_eligible_for_webbank = False
    if is_amor108_member and not is_webbank_member:
        amor108_member_instance = user.amor108_member
        if (amor108_member_instance.pool and 
            amor108_member_instance.pool.name.upper() == 'GOLD'):
            is_eligible_for_webbank = True
            
    available_credit = total_shares * settings.LOAN_TO_SHARE_MULTIPLIER - outstanding_loan_amount
    available_credit = max(available_credit, Decimal('0.00'))
    
    context = {
        'total_shares': total_shares,
        'active_loans': active_loans_count,
        'outstanding_loan_amount': outstanding_loan_amount,
        'available_credit': available_credit,
        'recent_transactions': recent_transactions,
        'active_loans_list': active_user_loans,
        'user_type': user.user_type,
        'is_webbank_member': is_webbank_member,
        'is_eligible_for_webbank': is_eligible_for_webbank,
    }
    
    return render(request, 'dashboard/dashboard.html', context)