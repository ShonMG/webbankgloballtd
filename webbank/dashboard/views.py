from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from shares.models import Share
from loans.models import Loan
from shares.models import ShareTransaction
# from accounts.decorators import user_type_required # Removed this import

@login_required
# @user_type_required(['member', 'director', 'guarantor']) # Removed this decorator
def main_dashboard(request):
    user = request.user
    
    # Redirect admin to their specific dashboard
    if user.user_type == 'admin':
        return redirect('admin_panel:admin_dashboard')
    
    # Redirect founder to their specific dashboard
    if user.user_type == 'founder':
        return redirect('admin_panel:founder_dashboard') # Assuming a founder_dashboard exists
    
    # Calculate dashboard statistics
    try:
        total_shares = user.share.total_value
    except Share.DoesNotExist:
        total_shares = 0
    active_loans = Loan.objects.filter(member=user, status__in=['active', 'disbursed']).count()
    outstanding_loan_amount = Loan.objects.filter(
        member=user, 
        status__in=['active', 'disbursed']
    ).aggregate(total=Sum('amount_approved'))['total'] or 0
    
    # Calculate available credit (3x shares value)
    available_credit = total_shares * 3 - outstanding_loan_amount
    available_credit = max(available_credit, 0)
    
    # Recent activity
    recent_transactions = ShareTransaction.objects.filter(member=user).order_by('-transaction_date')[:5]
    
    # Loan progress
    active_user_loans = Loan.objects.filter(member=user, status__in=['active', 'disbursed'])
    
    context = {
        'total_shares': total_shares,
        'active_loans': active_loans,
        'outstanding_loan_amount': outstanding_loan_amount,
        'available_credit': available_credit,
        'recent_transactions': recent_transactions,
        'active_loans_list': active_user_loans,
        'user_type': user.user_type,
    }
    
    return render(request, 'dashboard/dashboard.html', context)