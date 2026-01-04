from collections import defaultdict # Import defaultdict for easy grouping
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView # Import Django's default LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm # Add this import
from django.contrib import messages # Import messages for user feedback

from .decorators import admin_required, pool_manager_required # Keep decorators for sample view

from .forms import Amor108AuthenticationForm, Amor108RegistrationForm, Amor108ProfileUpdateForm # Updated form class
from .models import LoginHistory
from pools.models import Pool # Import the Pool model

class Amor108SignUpView(CreateView):
    form_class = Amor108RegistrationForm # Use the new form
    success_url = reverse_lazy('accounts_amor108:login')
    template_name = 'accounts_amor108/signup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['signup_form'] = context['form']

        # Group form choices by category for display
        categorized_membership_choices = defaultdict(list)
        # Assuming choice.choice_label is formatted as "CATEGORY_NAME: DESCRIPTION"
        for choice in context['signup_form']['membership_pool']:
            # Extract category name. Handle cases where ':' might not be present.
            parts = choice.choice_label.split(':', 1) # Split only on the first colon
            category_name = parts[0].strip() if parts else "Uncategorized"
            categorized_membership_choices[category_name].append(choice)
        
        context['categorized_membership_choices'] = dict(categorized_membership_choices)

        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class Amor108LoginView(LoginView): # Revert to Django's default LoginView
    authentication_form = Amor108AuthenticationForm # Changed to use custom AuthenticationForm
    template_name = 'accounts_amor108/login.html' # You'll need to create this template
    
    def get_success_url(self):
        return reverse_lazy('amor108:dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form) # Call the parent's form_valid
        # Record login history
        LoginHistory.objects.create(
            user=form.get_user(),
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT')
        )
        return response

def amor108_logout_view(request):
    logout(request)
    return redirect(reverse_lazy('accounts_amor108:login')) # Redirect to login page after logout

# Profile setup view
@login_required
def profile_setup_view(request):
    user = request.user
    
    # Ensure the user has an Amor108Member instance
    if not hasattr(user, 'amor108_member'):
        messages.error(request, "Your Amor108 profile is not fully set up. Please contact support.")
        return redirect('amor108:index') # Or a more appropriate redirect

    if request.method == 'POST':
        form = Amor108ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('amor108:dashboard') # Redirect to Amor108 dashboard after setup
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = Amor108ProfileUpdateForm(instance=user)
    
    return render(request, 'accounts_amor108/profile_setup.html', {'form': form})


# You might also want to create a dashboard view or profile view for Amor108 users
@login_required
def amor108_dashboard(request):
    return render(request, 'accounts_amor108/dashboard.html') # Create this template as well

@login_required
@admin_required
@pool_manager_required
def amor108_admin_panel(request):
    """
    A sample view that demonstrates role-based access control.
    Only accessible by users with 'Admin' or 'Pool Manager' role.
    """
    return render(request, 'accounts_amor108/admin_panel.html', {
        'message': 'Welcome to the Amor108 Admin/Pool Manager Panel!'
    })

@login_required
def amor108_loan_option(request):
    """
    Directs users to Amor108 loan request if they are an approved member,
    otherwise prompts them to sign up.
    """
    if hasattr(request.user, 'amor108_profile') and request.user.amor108_profile.is_approved:
        # If the user is an approved Amor108 member, redirect to loan request
        return redirect('amor108:loan_request')
    else:
        # If not an approved member, redirect to signup/pending approval page
        messages.info(request, "You must be an approved Amor108 member to request a loan. Please sign up or await approval.")
        return redirect(reverse_lazy('accounts_amor108:signup'))