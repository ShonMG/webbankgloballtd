from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db.models import Sum
from accounts_amor108.decorators import member_approval_required
from pools.models import Pool
from loans.models import Loan
from contributions.models import Contribution
from guarantees.models import Guarantee
from loans.forms import Amor108LoanApplicationForm as LoanForm
from contributions.forms import ContributionForm
from accounts_amor108.forms import Amor108RegistrationForm, Amor108AuthenticationForm as LoginForm
from members_amor108.models import Member
from shares.models import Share
from profits.models import MemberProfit
from decimal import Decimal
from django.utils import timezone

# Helper function to get base context for all dashboard pages
def get_base_dashboard_context(member):
    # This can be expanded to include any context needed on all dashboard pages,
    # like notifications, user info, etc.
    total_contributions_val = Contribution.objects.filter(member=member).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    share, _ = Share.objects.get_or_create(member=member)
    current_share_value_val = share.total_value
    total_interest_earned_val = MemberProfit.objects.filter(member=member, action__in=['WITHDRAWN', 'REINVESTED']).aggregate(Sum('net_profit'))['net_profit__sum'] or Decimal('0.00')
    active_loans_balance_val = Loan.objects.filter(amor108_member=member, status='active').aggregate(Sum('amount_approved'))['amount_approved__sum'] or Decimal('0.00')
    
    return {
        'member': member,
        'is_amor108_dashboard': True,
        'total_contributions': total_contributions_val,
        'current_share_value': current_share_value_val,
        'accrued_interest': total_interest_earned_val,
        'active_loans_balance': active_loans_balance_val,
    }

def index(request):
    if request.user.is_authenticated and hasattr(request.user, 'amor108_profile'):
        if request.user.amor108_profile.is_approved:
            return redirect('amor108:dashboard')
        else:
            return render(request, 'amor108/pending_approval.html', {'message': 'Your account is awaiting approval.'})

    if request.method == 'POST':
        signup_form = Amor108RegistrationForm(request.POST, request.FILES)
        if signup_form.is_valid():
            signup_form.save()
            messages.success(request, 'Registration successful! Your account is awaiting approval.')
            return redirect('amor108:signin')
    else:
        signup_form = Amor108RegistrationForm()
    
    return render(request, 'amor108/index.html', {'signup_form': signup_form})

def signin(request):
    if request.user.is_authenticated and hasattr(request.user, 'amor108_profile'):
        return redirect('amor108:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if hasattr(user, 'amor108_profile') and user.amor108_profile.is_approved:
                    login(request, user)
                    return redirect('amor108:dashboard')
                else:
                    messages.error(request, 'Your account is not yet approved.')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()
    
    return render(request, 'amor108/signin.html', {'form': form})

def pool_list(request):
    pools = Pool.objects.all()
    return render(request, 'amor108/pools.html', {'pools': pools})

def pool_detail(request, pool_id):
    pool = Pool.objects.get(id=pool_id)
    members = Member.objects.filter(pool=pool)
    return render(request, 'amor108/pool_detail.html', {'pool': pool, 'members': members})

@login_required
@member_approval_required
def loan_request(request):
    if request.method == 'POST':
        form = LoanForm(request.POST, user=request.user)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.amor108_member = request.user.amor108_member
            loan.save()
            form.save_m2m()
            messages.success(request, 'Loan application submitted successfully.')
            return redirect('amor108:dashboard_loans')
    else:
        form = LoanForm(user=request.user)
    return render(request, 'amor108/loan_form.html', {'form': form})

# --- Refactored Dashboard Views ---

@login_required
@member_approval_required
def dashboard(request):
    # This view now only handles the main profile page
    context = get_base_dashboard_context(request.user.amor108_member)
    context['active_page'] = 'profile'
    # Add any other profile-specific context if needed
    context['member'] = request.user.amor108_member
    return render(request, 'amor108/dashboard.html', context)

@login_required
@member_approval_required
def dashboard_contributions(request):
    from contributions.views import get_contribution_summary
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'contributions'
    
    contribution_summary = get_contribution_summary(member)
    context.update(contribution_summary)
    
    return render(request, 'amor108/dashboard_contributions.html', context)

@login_required
@member_approval_required
def dashboard_shares(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'shares'
    
    share, _ = Share.objects.get_or_create(member=member)
    reinvested_interest = MemberProfit.objects.filter(member=member, action='REINVESTED').aggregate(Sum('net_profit'))['net_profit__sum'] or Decimal('0.00')

    context.update({
        'total_shares_owned': share.units,
        'reinvested_interest_amount': reinvested_interest,
        'share_value_per_unit': share.unit_price,
        'total_share_value_tracker': share.total_value,
    })
    return render(request, 'amor108/dashboard_shares.html', context)

@login_required
@member_approval_required
def dashboard_loans(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'loans'

    context['active_loans'] = Loan.objects.filter(amor108_member=member, status__in=['active', 'disbursed']).order_by('-application_date')
    context['loan_history'] = Loan.objects.filter(amor108_member=member).exclude(status__in=['active', 'disbursed']).order_by('-application_date')
    
    return render(request, 'amor108/dashboard_loans.html', context)

@login_required
@member_approval_required
def dashboard_guarantees(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'guarantees'
    
    given_guarantees = Guarantee.objects.filter(guarantor=member.user)
    pending_guarantees_on_my_loans = Guarantee.objects.filter(loan__amor108_member=member, status='pending').exclude(guarantor=member.user)
    pending_guarantees_given_by_me = given_guarantees.filter(status='pending')
    
    context.update({
        'guarantees': given_guarantees,
        'all_pending_guarantees': (pending_guarantees_on_my_loans | pending_guarantees_given_by_me).distinct(),
        'total_guarantees': given_guarantees.count(),
        'active_guarantees': given_guarantees.filter(status='active').count(),
        'total_amount': given_guarantees.aggregate(total=Sum('amount_guaranteed'))['total'] or 0,
        'at_risk': given_guarantees.filter(loan__status='defaulted').count(),
    })
    return render(request, 'amor108/dashboard_guarantees.html', context)

# Add other placeholder views
@login_required
@member_approval_required
def dashboard_placeholder(request, page_name):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = page_name
    template_name = f'amor108/dashboard_{page_name}.html'
    # Add specific context for each page here if necessary
    return render(request, template_name, context)