from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
import time
import random
import string
from django.core.mail import send_mail # Import send_mail
from .models import User
from .forms import LoginForm, SignUpForm, ProfileUpdateForm, UserSettingsForm
from loans.models import Loan

# Default email for the webbank
DEFAULT_FROM_EMAIL = 'theibankdollars@gmail.com'

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard:main_dashboard')

    context = {
        'total_members': User.objects.filter(user_type='member').count(),
        'total_loan_payouts': Loan.objects.filter(status='disbursed').aggregate(total=Sum('amount_approved'))['total'] or 0,
        'years_active': 5 # Static for now
    }
    return render(request, 'index.html', context)

def signin(request):
    if request.user.is_authenticated:
        return redirect('dashboard:main_dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(username=email, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    return redirect('dashboard:main_dashboard')
                else:
                    messages.error(request, 'Invalid password.')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
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
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=user)
    
    return render(request, 'accounts/profile.html', {'form': form})

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

def prolink_network_detail(request):
    return render(request, 'accounts/prolink_network_detail.html')

def amor_108_inv_detail(request):
    return render(request, 'accounts/amor_108_inv_detail.html')