from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db.models import Sum
from django.db import transaction
import math
from accounts_amor108.decorators import member_approval_required
from pools.models import Pool
from loans.models import Loan
from contributions.models import Contribution
from guarantees.models import Guarantee
from shares.models import Share, ShareLock
from investments.models import Investment
from governance.models import Resolution
from loans.forms import Amor108LoanApplicationForm as LoanForm
from contributions.forms import ContributionForm
from accounts_amor108.forms import Amor108RegistrationForm, Amor108AuthenticationForm as LoginForm
from members_amor108.models import Member
from profits.models import MemberProfit
from decimal import Decimal
from django.utils import timezone
from django.urls import reverse # Import reverse
from notifications.models import Notification # Import Notification model for dashboard_notifications
from accounts.models import User # Added this import
from audit.models import AuditLog # Added this import
from documents.models import Document # Added this import
from support.models import SupportTicket # Added this import


# Helper function to get base context for all dashboard pages
def get_base_dashboard_context(member):
    # This can be expanded to include any context needed on all dashboard pages,
    # like notifications, user info, etc.
    total_contributions_val = Contribution.objects.filter(member=member).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    share, _ = Share.objects.get_or_create(member=member)
    total_shares_value_val = share.total_value # Renamed for clarity with template
    profit_balance_val = MemberProfit.objects.filter(member=member, action__in=['WITHDRAWN', 'REINVESTED']).aggregate(Sum('net_profit'))['net_profit__sum'] or Decimal('0.00')
    active_loans_balance_val = Loan.objects.filter(amor108_member=member, status='active').aggregate(Sum('amount_approved'))['amount_approved__sum'] or Decimal('0.00')
    
    # New: Guarantees Exposure for summary cards
    guarantees_given = Guarantee.objects.filter(guarantor=member.user)
    guarantees_exposure_val = guarantees_given.filter(status='active').aggregate(Sum('amount_guaranteed'))['amount_guaranteed__sum'] or Decimal('0.00')

    return {
        'member': member,
        'is_amor108_dashboard': True,
        'total_contributions': total_contributions_val,
        'total_shares_value': total_shares_value_val, # Renamed for clarity with template
        'profit_balance': profit_balance_val, # Renamed for clarity with template
        'active_loans_balance': active_loans_balance_val,
        'guarantees_exposure': guarantees_exposure_val, # Added
        'member_status': member.status.name, # Added for summary card
        'pool_type': member.pool.name, # Added for summary card
    }

def get_recent_activities(member, limit=5):
    activities = []
    
    # Recent Contributions
    for contribution in Contribution.objects.filter(member=member).order_by('-date')[:limit]:
        activities.append({
            'timestamp': contribution.date,
            'description': f"Contributed Ksh {contribution.amount} to {contribution.member.pool.name} pool.",
            'category': 'Contribution',
            'link': reverse('amor108:dashboard_contributions') # Assuming there's a view for contributions
        })

    # Recent Loan Applications/Updates
    for loan in Loan.objects.filter(amor108_member=member).order_by('-application_date')[:limit]:
        status_display = loan.get_status_display()
        activities.append({
            'timestamp': loan.application_date,
            'description': f"Loan application for Ksh {loan.amount_requested} - Status: {status_display}",
            'category': 'Loan',
            'link': reverse('amor108:dashboard_loans') # Assuming there's a view for loans
        })
    
    # Recent Profit Actions (e.g., distribution, reinvestment)
    for profit in MemberProfit.objects.filter(member=member).order_by('-created_at')[:limit]:
        action_display = profit.get_action_display()
        activities.append({
            'timestamp': profit.created_at,
            'description': f"Profit action: {action_display} of Ksh {profit.net_profit}",
            'category': 'Profit',
            'link': reverse('amor108:dashboard_profits') # Assuming there's a view for profits
        })
        
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit] # Return overall top N activities


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

@login_required
def pending_approval_view(request):
    """
    Renders a page informing the user that their account is awaiting approval,
    and provides user and member details for display.
    """
    user = request.user
    member = None
    
    print(f"--- DEBUG in pending_approval_view: request.user = {user} ---")
    print(f"--- DEBUG in pending_approval_view: hasattr(user, 'amor108_member') = {hasattr(user, 'amor108_member')} ---")

    if hasattr(user, 'amor108_member'):
        member = user.amor108_member
    
    print(f"--- DEBUG in pending_approval_view: member = {member} ---")

    context = {
        'message': 'Your account is awaiting approval.',
        'user': user,
        'member': member,
    }
    return render(request, 'amor108/pending_approval.html', context)

def signin(request):
    if request.user.is_authenticated and hasattr(request.user, 'amor108_profile'):
        if request.user.amor108_profile.is_approved:
            return redirect('amor108:dashboard')
        else:
            # If authenticated but not approved, redirect to pending approval page
            return redirect('amor108:pending_approval')

    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST) # Corrected instantiation
        print("--- DEBUG: In amor108 signin POST request, before form.is_valid() ---") # Temporary debug print
        print("--- DEBUG: request.POST:", request.POST)
        print("--- DEBUG: form.data:", form.data)
        print("--- DEBUG: form.is_bound:", form.is_bound)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if hasattr(user, 'amor108_profile'):
                    if user.amor108_profile.is_approved:
                        login(request, user)
                        return redirect('amor108:dashboard')
                    else:
                        messages.error(request, 'Your account is not yet approved.')
                else:
                    # User authenticated but no amor108_profile. This should ideally not happen if registration works correctly.
                    # This could happen if users are created via admin or createsuperuser without an associated profile.
                    messages.error(request, 'Your account is not fully set up. Please contact support.')
            else:
                messages.error(request, 'Invalid credentials.')
        else: # Form is not valid
            print("Form errors (field-specific):", form.errors) # Debugging output to console
            print("Form errors (non-field):", form.non_field_errors()) # Debugging output for non-field errors
            messages.error(request, 'Please correct the errors below.')
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
def dashboard_home(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'dashboard'
    
    context['recent_activities'] = get_recent_activities(member) # Add recent activities
    
    return render(request, 'amor108/dashboard.html', context)

@login_required
@member_approval_required
def dashboard_profile(request):
    # This view now only handles the main profile page
    context = get_base_dashboard_context(request.user.amor108_member)
    context['active_page'] = 'profile'
    # Add any other profile-specific context if needed
    context['member'] = request.user.amor108_member
    return render(request, 'amor108/dashboard_profile.html', context)

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

    # Credit Power Indicator (Dummy Logic)
    # A more complex calculation would involve loan eligibility, risk assessment, etc.
    credit_power = share.total_value * Decimal('0.5') # 50% of share value as credit power
    
    # Share Purchase CTA (Dummy Logic for is_locked)
    # Shares cannot be withdrawn if active loan or active guarantee.
    # For purchase, we'll assume they can always purchase unless some other rule (not specified here) applies.
    has_active_loan = Loan.objects.filter(amor108_member=member, status__in=['active', 'disbursed']).exists()
    has_active_guarantee = Guarantee.objects.filter(guarantor=member.user, status='active').exists()
    
    can_withdraw_shares = not (has_active_loan or has_active_guarantee)

    context.update({
        'total_shares_owned': share.units,
        'reinvested_interest_amount': reinvested_interest,
        'share_value_per_unit': share.unit_price,
        'total_share_value_tracker': share.total_value,
        'credit_power': credit_power,
        'can_withdraw_shares': can_withdraw_shares,
        'can_purchase_shares': True, # For now, assume always true
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

@login_required
@member_approval_required
def dashboard_pools(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'pools'

    all_pools = Pool.objects.all().order_by('contribution_amount')
    member_pool = member.pool if member.pool else None

    # Dummy logic for pool upgrade eligibility
    can_upgrade = False
    next_pool_requirements = None
    if member_pool:
        # Example: if member is in a pool, check if there's a higher tier
        higher_pools = all_pools.filter(contribution_amount__gt=member_pool.contribution_amount).order_by('contribution_amount')
        if higher_pools.exists():
            can_upgrade = True
            next_pool = higher_pools.first()
            next_pool_requirements = {
                'name': next_pool.name,
                'contribution_amount': next_pool.contribution_amount,
                'member_limit': next_pool.member_limit,
                'description': next_pool.description,
            }

    context.update({
        'all_pools': all_pools,
        'member_pool': member_pool,
        'can_upgrade': can_upgrade,
        'next_pool_requirements': next_pool_requirements,
    })
    
    return render(request, 'amor108/dashboard_pools.html', context)



@login_required
@member_approval_required
def dashboard_voting(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'voting'

    all_resolutions = Resolution.objects.all().order_by('-creation_date')
    
    active_resolutions = []
    voting_history = []
    
    for res in all_resolutions:
        can_vote, reason = res.can_user_vote(request.user)
        user_has_voted = res.votes.filter(voter=request.user).exists()
        
        setattr(res, 'can_vote', can_vote)
        setattr(res, 'can_vote_reason', reason)
        setattr(res, 'user_has_voted', user_has_voted)
        
        if user_has_voted:
            setattr(res, 'user_vote', res.votes.get(voter=request.user))
        else:
            setattr(res, 'user_vote', None)

        if res.is_voting_open():
            active_resolutions.append(res)
        else:
            voting_history.append(res)

    context.update({
        'active_resolutions': active_resolutions,
        'voting_history': voting_history,
        'voting_power': member.share_account.total_value, # Dynamically calculated from shares
    })
    
    return render(request, 'amor108/dashboard_voting.html', context)


@login_required
@member_approval_required
def dashboard_transparency(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'transparency'

    # Dynamic data for transparency and audit
    # Assuming Documents with 'financial statement' in title (case-insensitive) are financial statements
    financial_statements = Document.objects.filter(
        owner__isnull=True,  # Public documents
        title__icontains='financial statement'
    ).order_by('-uploaded_at')[:5]
    if not financial_statements.exists(): # Fallback to description if no title match
        financial_statements = Document.objects.filter(
            owner__isnull=True,
            description__icontains='financial statement'
        ).order_by('-uploaded_at')[:5]

    # Assuming Documents with 'pool performance' in title (case-insensitive) and owned by the user are pool performance reports
    pool_performance_reports = Document.objects.filter(
        owner=request.user, # Documents related to the current member
        title__icontains='pool performance'
    ).order_by('-uploaded_at')[:5]
    if not pool_performance_reports.exists(): # Fallback to description if no title match
        pool_performance_reports = Document.objects.filter(
            owner=request.user,
            description__icontains='pool performance'
        ).order_by('-uploaded_at')[:5]


    admin_decisions = Resolution.objects.all().order_by('-creation_date')[:5] # All resolutions as admin decisions for now

    audit_logs = AuditLog.objects.filter(user=request.user).order_by('-timestamp')[:5] # Current user's audit logs

    context.update({
        'financial_statements': financial_statements,
        'pool_performance_reports': pool_performance_reports,
        'admin_decisions': admin_decisions,
        'audit_logs': audit_logs,
    })
    
    return render(request, 'amor108/dashboard_transparency.html', context)


@login_required
@member_approval_required
def dashboard_notifications(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'notifications'

    all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_notifications = all_notifications.filter(is_read=False)
    read_notifications = all_notifications.filter(is_read=True)

    context.update({
        'all_notifications': all_notifications,
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
    })
    
    return render(request, 'amor108/dashboard_notifications.html', context)

@login_required
@member_approval_required
def mark_all_notifications_as_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
    return redirect('amor108:dashboard_notifications')


@login_required
@member_approval_required
def dashboard_investments(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'investments'

    context['active_investments'] = Investment.objects.filter(member=member, status='active')
    context['investment_history'] = Investment.objects.filter(member=member).exclude(status='active')
    
    return render(request, 'amor108/dashboard_investments.html', context)


@login_required
@member_approval_required
def dashboard_documents(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'documents'

    context['available_documents'] = Document.objects.filter(owner__isnull=True).order_by('-uploaded_at')
    context['member_reports'] = Document.objects.filter(owner=request.user).order_by('-uploaded_at')
    
    return render(request, 'amor108/dashboard_documents.html', context)


@login_required
@member_approval_required
def dashboard_security(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'security'

    # Dynamic data for security settings
    # two_factor_enabled is on the User model
    two_factor_enabled = request.user.two_factor_enabled
    
    # Use last_login as a proxy for last_password_change if no dedicated field
    last_login_time = request.user.last_login if request.user.last_login else timezone.now() - timezone.timedelta(days=365) # Fallback to 1 year ago
    
    # Fetch recent login activities from AuditLog
    recent_logins = AuditLog.objects.filter(
        user=request.user, 
        action='LOGIN'
    ).order_by('-timestamp')[:5] # Get up to 5 most recent logins

    security_settings = {
        'two_factor_auth_enabled': two_factor_enabled,
        'last_password_change': last_login_time,
        'recent_logins': recent_logins, # This will now be a QuerySet of AuditLog objects
    }

    context.update({
        'security_settings': security_settings,
    })
    
    return render(request, 'amor108/dashboard_security.html', context)


@login_required
@member_approval_required
def dashboard_support(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'support'

    # Dynamic data for support tickets
    support_tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Placeholder/Dummy data for FAQs (since no FAQ model exists yet)
    faqs = [
        {'question': 'How do I contribute?', 'answer': 'You can contribute through M-Pesa STK Push.'},
        {'question': 'How do I apply for a loan?', 'answer': 'Navigate to the Loans section and fill the application form.'},
        {'question': 'What are the share withdrawal requirements?', 'answer': 'Minimum 30 days notice, no active loans or guarantees.'},
    ]

    context.update({
        'support_tickets': support_tickets,
        'faqs': faqs,
    })
    
    return render(request, 'amor108/dashboard_support.html', context)


@login_required
@member_approval_required
def dashboard_exit(request):
    member = request.user.amor108_member
    context = get_base_dashboard_context(member)
    context['active_page'] = 'exit'

    # Check for outstanding loans
    has_active_loans = Loan.objects.filter(amor108_member=member, status__in=['active', 'disbursed']).exists()
    
    # Check for active guarantees given by the member
    has_active_guarantees = Guarantee.objects.filter(guarantor=request.user, status='active').exists()
    
    # Determine if member can exit
    can_exit = not has_active_loans and not has_active_guarantees

    exit_requirements = []
    if has_active_loans:
        exit_requirements.append('All outstanding loans must be settled.')
    if has_active_guarantees:
        exit_requirements.append('No active guarantees.')
    exit_requirements.append('Minimum 30 days notice required for share withdrawal.')

    # Placeholder for current share value to be withdrawn
    share_account = Share.objects.filter(member=member).first()
    current_share_value = share_account.total_value if share_account else Decimal('0.00')

    withdrawal_options = [
        {'type': 'Full Share Withdrawal', 'description': f'Withdraw all your shares (Ksh {current_share_value}) and exit the Sacco.', 'available': can_exit},
        {'type': 'Partial Share Withdrawal', 'description': 'Withdraw a portion of your shares.', 'available': False}, # Dummy
    ]

    context.update({
        'can_exit': can_exit,
        'exit_requirements': exit_requirements,
        'withdrawal_options': withdrawal_options,
        'has_active_loans': has_active_loans,
        'has_active_guarantees': has_active_guarantees,
        'current_share_value': current_share_value,
    })
    
    return render(request, 'amor108/dashboard_exit.html', context)

@login_required
@member_approval_required
@transaction.atomic
def request_exit(request):
    if request.method == 'POST':
        member = request.user.amor108_member
        if member.status.name == 'PENDING_EXIT':
            messages.info(request, "You already have a pending exit request.")
            return redirect('amor108:dashboard_exit')
            
        # Check eligibility before allowing request (redundant with dashboard, but good practice)
        has_active_loans = Loan.objects.filter(amor108_member=member, status__in=['active', 'disbursed']).exists()
        has_active_guarantees = Guarantee.objects.filter(guarantor=request.user, status='active').exists()

        if has_active_loans or has_active_guarantees:
            messages.error(request, "You cannot request exit with outstanding loans or active guarantees.")
            return redirect('amor108:dashboard_exit')
            
        # Update member status
        member_status_pending_exit = Member.MEMBER_STATUS_CHOICES.get_or_create(name='PENDING_EXIT')[0]
        member.status = member_status_pending_exit
        member.save()
        
        # Notify governance members
        governance_users = User.objects.filter(user_type__in=['director', 'admin', 'founder'])
        for user in governance_users:
            Notification.objects.create(
                user=user,
                title='Member Exit Request',
                message=f"Member {member.user.username} has requested to exit the Sacco.",
                notification_type='info',
                related_object=member.user
            )
        messages.success(request, "Your exit request has been submitted successfully and is awaiting approval.")
    return redirect('amor108:dashboard_exit')


from django.http import HttpResponse
from django.shortcuts import get_object_or_404

@login_required
@member_approval_required
def reject_guarantee(request, guarantee_id):
    guarantee = get_object_or_404(Guarantee, id=guarantee_id)
    if guarantee.guarantor != request.user:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('amor108:dashboard_guarantees')
    
    if guarantee.status == 'pending':
        guarantee.status = 'rejected'
        guarantee.save()
        messages.success(request, f"You have rejected the guarantee for loan {guarantee.loan.loan_id}.")
    else:
        messages.warning(request, "This guarantee is no longer pending and cannot be rejected.")
        
    return redirect('amor108:dashboard_guarantees')

@login_required
@member_approval_required
@transaction.atomic
def accept_guarantee(request, guarantee_id):
    guarantee = get_object_or_404(Guarantee, id=guarantee_id)
    guarantor_member = request.user.amor108_member
    
    # Basic validation
    if guarantee.guarantor != request.user:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('amor108:dashboard_guarantees')
        
    if guarantee.status != 'pending':
        messages.warning(request, "This guarantee is no longer pending.")
        return redirect('amor108:dashboard_guarantees')

    loan = guarantee.loan
    pool = loan.amor108_member.pool

    # 1. Check if pool allows guarantees
    if not pool.allow_guarantees:
        messages.error(request, f"The pool '{pool.name}' does not allow guarantees.")
        return redirect('amor108:dashboard_guarantees')

    # 2. Check for exposure cap
    active_guarantees = Guarantee.objects.filter(guarantor=request.user, status='active')
    current_exposure = active_guarantees.aggregate(Sum('amount_guaranteed'))['amount_guaranteed__sum'] or Decimal('0.00')
    
    if current_exposure + guarantee.amount_guaranteed > pool.guarantee_exposure_limit:
        messages.error(request, f"Accepting this guarantee would exceed your exposure limit of Ksh {pool.guarantee_exposure_limit}.")
        return redirect('amor108:dashboard_guarantees')

    # 3. Check for available shares to lock
    share_account, _ = Share.objects.get_or_create(member=guarantor_member)
    
    # Calculate required shares to lock (e.g., 1 unit per 100 Ksh guaranteed)
    # This logic can be adjusted based on business rules
    required_locked_units = int(math.ceil(guarantee.amount_guaranteed / share_account.unit_price))

    # Calculate currently locked shares
    total_locked_units = ShareLock.objects.filter(share_account=share_account).aggregate(Sum('locked_units'))['locked_units__sum'] or 0

    available_units = share_account.units - total_locked_units

    if available_units < required_locked_units:
        messages.error(request, f"You do not have enough available shares to lock for this guarantee. Required: {required_locked_units}, Available: {available_units}.")
        return redirect('amor108:dashboard_guarantees')
        
    # All checks passed, proceed to accept
    try:
        # Create ShareLock
        ShareLock.objects.create(
            share_account=share_account,
            guarantee=guarantee,
            locked_units=required_locked_units
        )
        
        # Update guarantee status
        guarantee.status = 'active'
        guarantee.save()

        # Notify borrower (optional)
        Notification.objects.create(
            user=loan.amor108_member.user,
            message=f"Your loan request (ID: {loan.loan_id}) has been guaranteed by {guarantor_member.user.get_full_name()}."
        )

        messages.success(request, f"You have successfully accepted the guarantee for loan {loan.loan_id}.")

    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")

    return redirect('amor108:dashboard_guarantees')