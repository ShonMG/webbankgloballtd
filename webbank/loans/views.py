from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import time
import random
import string
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from decimal import Decimal
from django.contrib.auth import get_user_model

from .models import Loan, LoanType, LoanRepayment
from shares.models import Share
from members_amor108.models import Member as Amor108Member
from .forms import LoanApplicationForm, LoanRepaymentForm

User = get_user_model()

@login_required
def loans_dashboard(request):
    # This view redirects to my_loans, which is the comprehensive dashboard for logged-in users.
    return redirect('loans:my_loans')

def webbank_loan_request(request):
    user = request.user if request.user.is_authenticated else None
    
    # The guarantor search logic that was missing from the view.
    search_query = request.GET.get('guarantor_search', '')
    guarantors = None
    if search_query:
        guarantors = Amor108Member.objects.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        ).exclude(user=user).distinct() if user else Amor108Member.objects.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        ).distinct()

    paginator = Paginator(guarantors, 5) if guarantors else None
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number) if paginator else None
    
    if request.method == 'POST':
        # Get selected guarantors from the form submission to re-populate the checkboxes
        selected_guarantors = request.POST.getlist('guarantors')
        form = LoanApplicationForm(request.POST, user=user)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.interest_rate = loan.loan_type.interest_rate
            loan.approval_stage = 'pending_manager'
            loan.status = 'pending'
            
            if user:
                if hasattr(user, 'amor108_member'):
                    loan.amor108_member = user.amor108_member
                else:
                    loan.member = user
                
                loan.loan_id = f"WB-L{int(time.time())}{''.join(random.choices(string.digits, k=4))}"
                loan.approval_deadline = timezone.now() + timezone.timedelta(days=7)
                loan.save()
                form.save_m2m() # Save guarantors
                messages.success(request, 'Your loan application has been submitted successfully!')
                return redirect('loans:my_loans')
            else: # Guest user
                loan.loan_id = f"WB-GUEST-L{int(time.time())}"
                loan.save()
                # Guests can have guarantors selected, so save them.
                form.save_m2m()
                messages.success(request, 'Your loan application has been submitted successfully! We will contact you for further details.')
                return redirect('home')
    else:
        form = LoanApplicationForm(user=user)
        selected_guarantors = []

    context = {
        'form': form,
        'guarantors': page_obj,
        'search_query': search_query,
        'selected_guarantors': selected_guarantors,
    }
    return render(request, 'loans/webbank_loan_request.html', context)

@login_required
def my_loans(request):
    user = request.user
    
    # Determine which loans to fetch and what shares the user has
    user_loans_queryset = Loan.objects.none()
    outstanding_loan_amount = Decimal('0.00')
    total_shares = Decimal('0.00')

    if hasattr(user, 'amor108_member'):
        amor108_member_instance = user.amor108_member
        user_loans_queryset = Loan.objects.filter(amor108_member=amor108_member_instance).order_by('-application_date')
        try:
            total_shares = amor108_member_instance.share_account.total_value
        except Share.DoesNotExist:
            total_shares = Decimal('0.00')
        outstanding_loan_amount = user_loans_queryset.filter(status__in=['active', 'disbursed']).aggregate(total=Sum('outstanding_principal'))['total'] or Decimal('0.00')
    else:
        # Generic WebBank member has no shares, but can have loans
        user_loans_queryset = Loan.objects.filter(member=user).order_by('-application_date')
        outstanding_loan_amount = user_loans_queryset.filter(status__in=['active', 'disbursed']).aggregate(total=Sum('outstanding_principal'))['total'] or Decimal('0.00')

    available_credit = (total_shares * 3) - outstanding_loan_amount
    available_credit = max(available_credit, Decimal('0.00'))

    # The loan application form is handled by the `webbank_loan_request` view,
    # so we no longer need the form handling logic here.

    context = {
        'loans': user_loans_queryset,
        'outstanding_balance': outstanding_loan_amount,
        'available_credit': available_credit,
        'user_type': user.user_type,
    }
    return render(request, 'loans/loans.html', context)

@login_required
def repay_loan(request, pk):
    # This logic needs to find the loan regardless of member type
    try:
        if hasattr(request.user, 'amor108_member'):
            loan = get_object_or_404(Loan, pk=pk, amor108_member=request.user.amor108_member)
        else:
            loan = get_object_or_404(Loan, pk=pk, member=request.user)
    except Loan.DoesNotExist:
        messages.error(request, "Loan not found.")
        return redirect('loans:my_loans')

    if request.method == 'POST':
        form = LoanRepaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            if amount > loan.outstanding_principal:
                messages.error(request, "Repayment amount exceeds outstanding balance.")
                return redirect('loans:repay_loan', pk=loan.pk)

            messages.info(request, f"STK Push initiated for KES {amount} for loan {loan.loan_id}. Please approve the transaction on your phone.")

            LoanRepayment.objects.create(
                loan=loan,
                amount=amount,
                due_date=timezone.now().date(),
                status='paid',
                transaction_id=f"REPAY-{loan.loan_id}-{int(time.time())}"
            )
            
            # Recalculate outstanding balance and check if completed
            loan.save() # .save() will trigger balance calculation

            if loan.outstanding_principal <= 0:
                loan.status = 'completed'
                loan.save()

            messages.success(request, f"Successfully repaid KES {amount} for loan {loan.loan_id}.")
            return redirect('loans:my_loans')
    else:
        form = LoanRepaymentForm(initial={'amount': loan.outstanding_principal})
    
    context = {
        'loan': loan,
        'form': form,
        'user_type': request.user.user_type,
    }
    return render(request, 'loans/repay_loan.html', context)