from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
import time
import random
import string
from django.core.mail import send_mail # Import send_mail
import json
from .models import User, Testimonial # Import Testimonial
from .forms import LoginForm, SignUpForm, ProfileUpdateForm, UserSettingsForm
from loans.models import Loan, LoanType # Import LoanType
from members.models import Member as WebBankMember
from shares.models import Share # Import the Share model

# Default email for the webbank
DEFAULT_FROM_EMAIL = 'theibankdollars@gmail.com'

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard:main_dashboard')

    # Calculate total shares instead of total members
    total_shares_count = Share.objects.aggregate(total_units=Sum('units'))['total_units'] or 0
    total_loan_payouts = Loan.objects.filter(status='disbursed').aggregate(total=Sum('amount_approved'))['total'] or 0

    # Fetch approved testimonials
    testimonials = Testimonial.objects.filter(is_approved=True).select_related('member')[:2] # Limit to 2 for carousel

    # Fetch LoanType objects
    loan_types = LoanType.objects.all()
    loan_types_json = json.dumps([
        {
            'id': lt.id,
            'name': lt.name,
            'interest_rate': str(lt.interest_rate),
            'is_for_non_member': lt.is_for_non_member,
            'webbank_interest_share': str(lt.webbank_interest_share),
            'guarantor_interest_share': str(lt.guarantor_interest_share),
            'member_interest_share': str(lt.member_interest_share),
        } for lt in loan_types
    ])

    context = {
        'total_shares': total_shares_count,
        'total_loan_payouts': total_loan_payouts,
        'years_active': 5, # Static for now
        'testimonials': testimonials, # Pass testimonials to context
        'loan_types': loan_types, # Pass loan types to context
        'loan_types_json': loan_types_json,
    }
    return render(request, 'index.html', context)

def signin(request):
    if request.user.is_authenticated:
        return redirect('dashboard:main_dashboard')
    
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        print("--- DEBUG: In accounts signin POST request, before form.is_valid() ---") # Temporary debug print
        print("--- DEBUG: request.POST:", request.POST)
        print("--- DEBUG: form.data:", form.data)
        print("--- DEBUG: form.is_bound:", form.is_bound)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(username=email, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    
                    # Check if the user has an Amor108Profile
                    if hasattr(user, 'amor108_profile'):
                        if user.amor108profile.is_approved:
                            return redirect('amor108:dashboard')
                        else:
                            return redirect('amor108:pending_approval')
                    
                    # Default redirect for non-Amor108 members or if amor108profile doesn't exist
                    return redirect('dashboard:main_dashboard')
                else:
                    messages.error(request, 'Invalid password.')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
        else: # Form is not valid
            print("Form errors (field-specific):", form.errors) # Debugging output to console
            print("Form errors (non-field):", form.non_field_errors()) # Debugging output for non-field errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/signin.html', {'form': form})

def generate_member_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard:main_dashboard')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.member_id = generate_member_id()
            user.save()
            
            # Send welcome email
            subject = 'Welcome to WebBank - Account Awaiting Approval'
            message = (
                f'Dear {user.first_name},\n\n'
                'Thank you for registering with WebBank. Your account has been successfully created.\n'
                'Please note that your account is currently awaiting approval from our administration team.\n'
                'You will receive another email once your account has been approved and activated.\n\n'
                'Thank you for your patience.\n\n'
                'Sincerely,\n'
                'The WebBank Team'
            )
            recipient_list = [user.email]
            
            try:
                send_mail(subject, message, DEFAULT_FROM_EMAIL, recipient_list, fail_silently=False)
                messages.success(request, 'Account created successfully! A welcome email has been sent to you. Please await approval.')
            except Exception as e:
                messages.error(request, f'Account created, but failed to send welcome email. Error: {e}')
            
            # Do not log in the user immediately, as their account needs approval
            # login(request, user) # Remove this line
            
            return redirect('signin') # Redirect to signin page instead of create_profile
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')

@login_required
def profile(request):
    user = request.user
    
    is_amor108_member = hasattr(user, 'amor108_member')
    is_webbank_member = False
    amor108_pool = None
    
    if is_amor108_member:
        amor108_member_instance = user.amor108_member
        amor108_pool = amor108_member_instance.pool
        if WebBankMember.objects.filter(email=user.email, status='ACTIVE').exists():
            is_webbank_member = True

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=user)
    
    # Correctly calculate stats for the profile page
    total_shares = 0
    if is_amor108_member:
        try:
            total_shares = user.amor108_member.share_account.total_value
        except Exception:
            total_shares = 0

    loans = Loan.objects.filter(member=user) | Loan.objects.filter(amor108_member__user=user)
    active_loans_count = loans.filter(status__in=['active', 'disbursed']).count()
    outstanding_loan_amount = loans.filter(status__in=['active', 'disbursed']).aggregate(total=Sum('outstanding_principal'))['total'] or 0

    context = {
        'form': form,
        'is_amor108_member': is_amor108_member,
        'is_webbank_member': is_webbank_member,
        'amor108_pool': amor108_pool,
        'total_shares_value': total_shares,
        'active_loans_count': active_loans_count,
        'outstanding_loan_amount': outstanding_loan_amount,
    }
    
    return render(request, 'accounts/profile.html', context)

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

@login_required
def settings(request):
    user = request.user
    
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('accounts:settings')
    else:
        form = UserSettingsForm(instance=user)
    
    return render(request, 'accounts/settings.html', {'form': form})

@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! Update the session to prevent user from being logged out
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:settings')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})


def prolink_network_detail(request):
    return render(request, 'accounts/prolink_network_detail.html')

def amor_108_inv_detail(request):
    return render(request, 'accounts/amor_108_inv_detail.html')

def loan_options(request):
    """
    Presents the user with options to request a loan from WebBank or Amor108.
    """
    return render(request, 'accounts/loan_options.html')
