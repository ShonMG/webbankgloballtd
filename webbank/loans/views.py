from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone # Import timezone
import time
import random
import string
from .models import Loan, LoanType, LoanRepayment # Import LoanRepayment
from shares.models import Share
from django.db.models import Sum
from .forms import LoanApplicationForm, LoanRepaymentForm # Import LoanRepaymentForm

@login_required
def loans_dashboard(request):
    user = request.user
    user_loans = Loan.objects.filter(member=user).order_by('-application_date')
    loan_types = LoanType.objects.all()
    
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.member = user
            loan.loan_id = f"WB-L{int(time.time())}{''.join(random.choices(string.digits, k=4))}"
            loan.interest_rate = loan.loan_type.interest_rate
            loan.approval_stage = 'pending_manager' # Set initial approval stage
            loan.status = 'pending' # Set initial status
            loan.approval_deadline = timezone.now() + timezone.timedelta(days=7) # Set initial deadline
            loan.save()
            form.save_m2m() # Save ManyToMany relationships
            
            messages.success(request, 'Loan application submitted successfully!')
            return redirect('loans:loans_dashboard')
    else:
        form = LoanApplicationForm()
    
    # Calculate outstanding balance using an efficient database query
    outstanding_balance = user_loans.filter(
        status__in=['active', 'disbursed']
    ).aggregate(total=Sum('amount_approved'))['total'] or 0
    
    # Calculate available credit (3x shares minus outstanding loans)
    try:
        total_shares = user.share.total_value
    except Share.DoesNotExist:
        total_shares = 0
    
    available_credit = max((total_shares * 3) - outstanding_balance, 0)
    
    context = {
        'loans': user_loans,
        'outstanding_balance': outstanding_balance,
        'available_credit': available_credit,
        'loan_types': loan_types,
        'form': form,
        'user_type': user.user_type,
    }
    
    return render(request, 'loans/loans.html', context)


@login_required
def my_loans(request):
    user = request.user
    user_loans = Loan.objects.filter(member=user).order_by('-application_date')
    
    context = {
        'user_loans': user_loans,
        'user_type': user.user_type,
    }
    return render(request, 'loans/my_loans.html', context)

@login_required
def repay_loan(request, pk):
    loan = get_object_or_404(Loan, pk=pk, member=request.user)
    
    if request.method == 'POST':
        form = LoanRepaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            if amount > loan.remaining_balance:
                messages.error(request, "Repayment amount exceeds outstanding balance.")
                return redirect('loans:loan_detail', pk=loan.pk)

            # Placeholder for STK Push integration
            messages.info(request, f"STK Push initiated for KES {amount} for loan {loan.loan_id}. Please approve the transaction on your phone.")

            # Simulate successful payment and create repayment record
            LoanRepayment.objects.create(
                loan=loan,
                amount=amount,
                due_date=timezone.now().date(), # Assuming immediate payment
                status='paid',
                transaction_id=f"REPAY-{loan.loan_id}-{int(time.time())}"
            )
            
            # Update loan status if fully paid
            if loan.remaining_balance <= 0:
                loan.status = 'completed'
                loan.save()

            messages.success(request, f"Successfully repaid KES {amount} for loan {loan.loan_id}.")
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        form = LoanRepaymentForm(initial={'amount': loan.remaining_balance}) # Pre-fill with remaining balance
    
    context = {
        'loan': loan,
        'form': form,
        'user_type': request.user.user_type,
    }
    return render(request, 'loans/repay_loan.html', context)