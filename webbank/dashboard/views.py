from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from shares.models import Share
from loans.models import Loan
from shares.models import ShareTransaction
from decimal import Decimal
# from accounts.decorators import user_type_required # Removed this import

@login_required
def main_dashboard(request):
    user = request.user
    
    # Redirect admin to their specific dashboard
    if user.user_type == 'admin':
        return redirect('admin_panel:admin_dashboard')
    
    # Redirect founder to their specific dashboard
    if user.user_type == 'founder':
        return redirect('admin_panel:founder_dashboard')
    
    total_shares = Decimal('0.00')
    active_loans_count = 0
    outstanding_loan_amount = Decimal('0.00')
    recent_transactions = []
    active_user_loans = []

    # Check if the user is an AMOR108 member
    if hasattr(user, 'amor108_member'):
        amor108_member_instance = user.amor108_member
        
        try:
            # Shares are only for AMOR108 members
            total_shares = amor108_member_instance.share_account.total_value
        except Share.DoesNotExist:
            total_shares = Decimal('0.00')
            
        # Loans associated with Amor108Member
        active_loans_count = Loan.objects.filter(amor108_member=amor108_member_instance, status__in=['active', 'disbursed']).count()
        outstanding_loan_amount = Loan.objects.filter(
            amor108_member=amor108_member_instance, 
            status__in=['active', 'disbursed']
        ).aggregate(total=Sum('amount_approved'))['total'] or Decimal('0.00')
        
        recent_transactions = ShareTransaction.objects.filter(member=amor108_member_instance).order_by('-transaction_date')[:5]
        active_user_loans = Loan.objects.filter(amor108_member=amor108_member_instance, status__in=['active', 'disbursed'])
    else:
        # If not an AMOR108 member, they are a generic WebBank member.
        # Shares are 0 for them, as they don't have a share_account.
        total_shares = Decimal('0.00') # Explicitly set for clarity
        
        # Loans associated with generic User
        active_loans_count = Loan.objects.filter(member=user, status__in=['active', 'disbursed']).count()
        outstanding_loan_amount = Loan.objects.filter(
            member=user, 
            status__in=['active', 'disbursed']
        ).aggregate(total=Sum('amount_approved'))['total'] or Decimal('0.00')
        
        recent_transactions = [] # Generic members don't have share transactions
        active_user_loans = Loan.objects.filter(member=user, status__in=['active', 'disbursed'])
    
    # Calculate available credit (3x shares value) - applies regardless of Amor108Member presence
    # This calculation logic might need to be reconsidered if available_credit calculation
    # is different for non-AMOR108 members. For now, using existing logic.
    available_credit = total_shares * 3 - outstanding_loan_amount
    available_credit = max(available_credit, Decimal('0.00'))
    
    context = {
        'total_shares': total_shares,
        'active_loans': active_loans_count,
        'outstanding_loan_amount': outstanding_loan_amount,
        'available_credit': available_credit,
        'recent_transactions': recent_transactions,
        'active_loans_list': active_user_loans,
        'user_type': user.user_type,
    }
    
    return render(request, 'dashboard/dashboard.html', context)