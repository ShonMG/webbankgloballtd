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
from django.conf import settings

from .models import Loan, LoanType, LoanRepayment
from shares.models import Share
from members_amor108.models import Member as Amor108Member
from .forms import LoanApplicationForm, LoanRepaymentForm
from webbankboard.models import WebBankMembership

User = get_user_model()

@login_required
def loans_dashboard(request):
    user = request.user
    is_amor108_member = hasattr(user, 'amor108_member')
    is_webbank_member = False

    # Consistent membership check using email
    if is_amor108_member and WebBankMembership.objects.filter(user=user, status=WebBankMembership.StatusChoices.ACTIVE).exists():
        is_webbank_member = True

    user_loans_queryset = Loan.objects.none()
    outstanding_loan_amount = Decimal('0.00')
    total_shares = Decimal('0.00')

    if is_amor108_member:
        amor108_member_instance = user.amor108_member
        amor108_loans = Loan.objects.filter(amor108_member=amor108_member_instance)
        user_loans_queryset = user_loans_queryset | amor108_loans
        try:
            total_shares = amor108_member_instance.share_account.total_value
        except (Share.DoesNotExist, AttributeError):
            total_shares = Decimal('0.00')

    if is_webbank_member:
        webbank_loans = Loan.objects.filter(member=user)
        user_loans_queryset = user_loans_queryset | webbank_loans

    user_loans_queryset = user_loans_queryset.distinct().order_by('-application_date')
    
    outstanding_loan_amount = user_loans_queryset.filter(
        status__in=['active', 'disbursed']
    ).aggregate(total=Sum('outstanding_principal'))['total'] or Decimal('0.00')
    
    available_credit = (total_shares * settings.LOAN_TO_SHARE_MULTIPLIER) - outstanding_loan_amount
    available_credit = max(available_credit, Decimal('0.00'))

    context = {
        'loans': user_loans_queryset,
        'outstanding_balance': outstanding_loan_amount,
        'available_credit': available_credit,
        'user_type': user.user_type,
        'is_webbank_member': is_webbank_member,
        'is_amor108_member': is_amor108_member,
    }
    return render(request, 'loans/loans.html', context)

@login_required
def webbank_loan_request(request):
    is_guest_loan = request.GET.get('guest') == 'true'
    form_user = None if is_guest_loan else request.user

    # LAW 6: Guest loans must be sponsored by a WebBank member
    if is_guest_loan:
        if not WebBankMembership.objects.filter(user=request.user, status=WebBankMembership.StatusChoices.ACTIVE).exists():
            messages.error(request, "You must be an active WebBank member to sponsor a guest loan.")
            return redirect('loans:loans_dashboard')

    search_query = request.GET.get('guarantor_search', '')
    guarantors = None
    if search_query:
        guarantors = Amor108Member.objects.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        ).exclude(user=request.user).distinct() if request.user.is_authenticated else Amor108Member.objects.none()

    paginator = Paginator(guarantors, 5) if guarantors else None
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number) if paginator else None
    
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, user=form_user, is_guest_loan=is_guest_loan)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.loan_id = f"WB-L{int(time.time())}{''.join(random.choices(string.digits, k=4))}"
            loan.approval_deadline = timezone.now() + timezone.timedelta(days=7)
            
            if form_user:
                if hasattr(form_user, 'amor108_member'):
                    loan.amor108_member = form_user.amor108_member
                else:
                    loan.member = form_user
            
            if is_guest_loan and request.user.is_authenticated:
                loan.sponsored_by = request.user
            
            loan.save()
            form.save_m2m()
            messages.success(request, 'Your loan application has been submitted successfully!')
            return redirect('loans:my_loans')
    else:
        form = LoanApplicationForm(user=form_user, is_guest_loan=is_guest_loan)

    context = {
        'form': form,
        'is_guest_loan': is_guest_loan,
        'guarantors': page_obj,
        'search_query': search_query,
    }
    return render(request, 'loans/webbank_loan_request.html', context)

@login_required
def my_loans(request):
    user = request.user
    is_amor108_member = hasattr(user, 'amor108_member')
    is_webbank_member = False
    is_eligible_for_webbank = False

    if is_amor108_member:
        amor108_member_instance = user.amor108_member
        if WebBankMembership.objects.filter(user=user, status=WebBankMembership.StatusChoices.ACTIVE).exists():
            is_webbank_member = True
        elif (amor108_member_instance.pool and 
              amor108_member_instance.pool.name.upper() == 'GOLD'):
            is_eligible_for_webbank = True

    user_loans_queryset = Loan.objects.none()
    if is_amor108_member:
        user_loans_queryset = user_loans_queryset | Loan.objects.filter(amor108_member=user.amor108_member)
    if is_webbank_member:
        user_loans_queryset = user_loans_queryset | Loan.objects.filter(member=user)
        
    user_loans_queryset = user_loans_queryset.distinct().order_by('-application_date')

    context = {
        'user_loans': user_loans_queryset,
        'user_type': user.user_type,
        'is_webbank_member': is_webbank_member,
        'is_amor108_member': is_amor108_member,
        'is_eligible_for_webbank': is_eligible_for_webbank,
    }
    return render(request, 'loans/my_loans.html', context)

@login_required
def repay_loan(request, pk):
    try:
        loan = get_object_or_404(Loan, pk=pk)
        # Security check: ensure the loan belongs to the user
        if not (loan.amor108_member and loan.amor108_member.user == request.user) and not (loan.member == request.user):
            messages.error(request, "Loan not found or you do not have permission to view it.")
            return redirect('loans:my_loans')
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

            # Create repayment record
            LoanRepayment.objects.create(
                loan=loan,
                amount=amount,
                status='paid', # Assuming direct payment for now
                transaction_id=f"REPAY-{loan.loan_id}-{int(time.time())}"
            )
            
            loan.save() # Trigger balance recalculation
            messages.success(request, f"Successfully recorded payment of KES {amount} for loan {loan.loan_id}.")
            return redirect('loans:my_loans')
    else:
        form = LoanRepaymentForm(initial={'amount': loan.outstanding_principal})
    
    context = {
        'loan': loan,
        'form': form,
    }
    return render(request, 'loans/repay_loan.html', context)

@login_required
def loan_repayment_schedule(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    # Security check
    if not (loan.amor108_member and loan.amor108_member.user == request.user) and not (loan.member == request.user):
        messages.error(request, "You are not authorized to view this repayment schedule.")
        return redirect('loans:my_loans')

    repayments = loan.repayments.all().order_by('due_date')
    
    context = {
        'loan': loan,
        'repayments': repayments,
    }
    return render(request, 'loans/loan_repayment_schedule.html', context)