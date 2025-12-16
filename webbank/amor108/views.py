from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login # Keep login and authenticate, remove logout
from django.db.models import Sum # Import Sum
from .models import Pool, Member, Loan, Contribution
from .forms import LoanForm, ContributionForm, Amor108RegistrationForm, LoginForm

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard:main_dashboard')

    signup_form = Amor108RegistrationForm()

    if request.method == 'POST':
        signup_form = Amor108RegistrationForm(request.POST, request.FILES)
        if signup_form.is_valid():
            signup_form.save()
            messages.success(request, 'Registration successful! Your account is awaiting approval. Please sign in after approval.')
            return redirect('amor108:signin')
        else:
            messages.error(request, 'Please correct the errors below in the registration form.')
    
    context = {
        'signup_form': signup_form,
    }
    return render(request, 'amor108/index.html', context)

def pool_list(request):
    pools = Pool.objects.all()
    return render(request, 'amor108/pools.html', {'pools': pools})

def pool_detail(request, pool_id):
    pool = Pool.objects.get(id=pool_id)
    members = Member.objects.filter(pool=pool)
    return render(request, 'amor108/pool_detail.html', {'pool': pool, 'members': members})

@login_required
def loan_request(request):
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.member = request.user.member
            form.save()
            return redirect('amor108:index')
    else:
        form = LoanForm()
    return render(request, 'amor108/loan_form.html', {'form': form})

@login_required
def make_contribution(request):
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.member = request.user.member
            form.save()
            return redirect('amor108:index')
    else:
        form = ContributionForm()
    return render(request, 'amor108/contribution_form.html', {'form': form})

def signin(request):
    if request.user.is_authenticated:
        return redirect('dashboard:main_dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('amor108:dashboard')
            else:
                messages.error(request, 'Invalid credentials for sign in.')
    else:
        form = LoginForm()
    
    return render(request, 'amor108/signin.html', {'form': form})

@login_required
def dashboard(request):
    member = request.user.member
    
    # Dashboard Overview (Summary Cards)
    total_contributions = Contribution.objects.filter(member=member).aggregate(Sum('amount'))['amount__sum'] or 0
    current_share_value = 0 # Placeholder for now, will come from Shares app
    accrued_interest = 0 # Placeholder for now
    active_loans_balance = Loan.objects.filter(member=member, status='active').aggregate(Sum('amount'))['amount__sum'] or 0
    available_loan_limit = 0 # Placeholder for now

    # Member Profile Section (data already available via 'member' object)

    # Contributions & Savings Section
    all_contributions = Contribution.objects.filter(member=member).order_by('-date')
    total_contributions_to_date = total_contributions # Same as total_contributions for now

    # Simplified placeholders for consistency and missed/late contributions
    # Real implementation would require more complex date calculations and expected schedule
    expected_contribution_amount = member.pool.contribution_amount
    expected_contribution_frequency = member.pool.get_contribution_frequency_display()
    contribution_consistency = "N/A" # Placeholder
    missed_late_contributions_count = "N/A" # Placeholder

    # Shares & Growth Tracker Section (Placeholders)
    total_shares_owned = 100 # Placeholder
    reinvested_interest_amount = 0 # Placeholder
    share_value_per_unit = 100 # Placeholder
    total_share_value_tracker = total_shares_owned * share_value_per_unit # Placeholder
    # Share Growth Over Time (Chart) - will be handled in template with JS

    # Loans Section
    active_loans = Loan.objects.filter(member=member, status__in=['active', 'disbursed']).order_by('-date')
    loan_history = Loan.objects.filter(member=member).exclude(status__in=['active', 'disbursed']).order_by('-date')

    # Profit & Interest Distribution (Placeholders)
    total_interest_earned = 0 # Placeholder
    current_year_profit = 0 # Placeholder
    last_distribution_amount = 0 # Placeholder
    next_distribution_date = "N/A" # Placeholder

    # Investments & Pool Performance (Placeholders)
    pool_total_fund_value = 0 # Placeholder
    active_investments = "N/A" # Placeholder (e.g., "Stocks, Real Estate")
    pool_returns_generated = 0 # Placeholder
    members_share_of_pool_returns = 0 # Placeholder

    # Voting & Governance (Placeholders)
    active_proposals = [] # Placeholder
    voting_history = [] # Placeholder
    voting_power = "N/A" # Placeholder

    # Notifications & Alerts (Placeholders)
    notifications = [
        {'message': 'Your contribution of Ksh 5000 is due on 2025-01-01', 'type': 'reminder'},
        {'message': 'Your loan repayment of Ksh 1000 is due on 2025-01-05', 'type': 'alert'},
        {'message': 'Profit distribution for Q4 2024 has been processed', 'type': 'notice'},
    ]

    # Documents & Reports (Placeholders)
    documents_reports = [
        {'name': 'Membership Agreement', 'url': '#', 'format': 'PDF'},
        {'name': 'Terms & Conditions', 'url': '#', 'format': 'PDF'},
        {'name': 'Annual Financial Report 2024', 'url': '#', 'format': 'PDF'},
        {'name': 'Personal Statement Q3 2024', 'url': '#', 'format': 'Excel'},
    ]

    # Exit & Withdrawal Section (Placeholders)
    exit_notice_date = "N/A" # Placeholder
    countdown_timer = "N/A" # Placeholder (e.g., "30 days remaining")
    estimated_withdrawal_amount = 0 # Placeholder
    outstanding_obligations_summary = "N/A" # Placeholder

    # Support & Communication (Placeholders)
    message_pool_manager_link = "#" # Placeholder
    contact_admin_link = "#" # Placeholder
    faqs_link = "#" # Placeholder
    help_tickets_link = "#" # Placeholder

    # Security & Settings (Placeholders)
    change_password_link = "#" # Placeholder
    two_factor_auth_status = "Disabled" # Placeholder
    device_login_history_link = "#" # Placeholder
    notification_preferences_link = "#" # Placeholder
    logout_link = "#" # Placeholder

    # Transparency & Trust Indicators (Placeholders)
    last_audit_date = "N/A" # Placeholder
    last_financial_update = "N/A" # Placeholder
    system_health_status = "Operational" # Placeholder
    verified_payment_status = "Verified" # Placeholder
    
    context = {
        'member': member,
        'is_amor108_dashboard': True,
        # Summary Cards
        'total_contributions': total_contributions,
        'current_share_value': current_share_value,
        'accrued_interest': accrued_interest,
        'active_loans_balance': active_loans_balance,
        'available_loan_limit': available_loan_limit,
        'pool_name': member.pool.name,
        'member_status': member.status,

        # Member Profile Details
        # These are already accessible via member.user and member.pool

        # Contributions & Savings
        'all_contributions': all_contributions,
        'total_contributions_to_date': total_contributions_to_date,
        'expected_contribution_amount': expected_contribution_amount,
        'expected_contribution_frequency': expected_contribution_frequency,
        'contribution_consistency': contribution_consistency,
        'missed_late_contributions_count': missed_late_contributions_count,

        # Shares & Growth Tracker
        'total_shares_owned': total_shares_owned,
        'reinvested_interest_amount': reinvested_interest_amount,
        'share_value_per_unit': share_value_per_unit,
        'total_share_value_tracker': total_share_value_tracker,

        # Loans Section
        'active_loans': active_loans,
        'loan_history': loan_history,

        # Profit & Interest Distribution
        'total_interest_earned': total_interest_earned,
        'current_year_profit': current_year_profit,
        'last_distribution_amount': last_distribution_amount,
        'next_distribution_date': next_distribution_date,

        # Investments & Pool Performance
        'pool_total_fund_value': pool_total_fund_value,
        'active_investments': active_investments,
        'pool_returns_generated': pool_returns_generated,
        'members_share_of_pool_returns': members_share_of_pool_returns,

        # Voting & Governance
        'active_proposals': active_proposals,
        'voting_history': voting_history,
        'voting_power': voting_power,

        # Notifications & Alerts
        'notifications': notifications,

        # Documents & Reports
        'documents_reports': documents_reports,

        # Exit & Withdrawal Section
        'exit_notice_date': exit_notice_date,
        'countdown_timer': countdown_timer,
        'estimated_withdrawal_amount': estimated_withdrawal_amount,
        'outstanding_obligations_summary': outstanding_obligations_summary,

        # Support & Communication
        'message_pool_manager_link': message_pool_manager_link,
        'contact_admin_link': contact_admin_link,
        'faqs_link': faqs_link,
        'help_tickets_link': help_tickets_link,

        # Security & Settings
        'change_password_link': change_password_link,
        'two_factor_auth_status': two_factor_auth_status,
        'device_login_history_link': device_login_history_link,
        'notification_preferences_link': notification_preferences_link,
        'logout_link': logout_link,

        # Transparency & Trust Indicators
        'last_audit_date': last_audit_date,
        'last_financial_update': last_financial_update,
        'system_health_status': system_health_status,
        'verified_payment_status': verified_payment_status,
    }
    return render(request, 'amor108/dashboard.html', context)