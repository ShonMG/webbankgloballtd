from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy # Import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages # Import messages for user feedback
from django.utils import timezone
from datetime import timedelta, date
import uuid # For generating dummy transaction codes
from decimal import Decimal
from django.db import models
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import AccessMixin
from django.db.models import Q # Import Q object for complex queries
from django.http import JsonResponse # Import JsonResponse for callback
from dateutil.relativedelta import relativedelta # For date calculations

from .forms import ContributionForm
from .models import Contribution, ContributionStatus
from members_amor108.models import Member as Amor108Member # Redundant import? Use Amor108Profile directly
from accounts_amor108.models import Amor108Profile # Import Amor108Profile
from .utils import get_next_expected_contribution_date # Import the utility function

class Amor108MemberRequiredMixin(AccessMixin):
    """Verify that the current user is an AMOR108 member or staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Allow staff/admins to view pages
        if request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'amor108_profile'):
            messages.error(request, "You need to complete your Amor108 profile to access contribution features.")
            return redirect('accounts_amor108:profile_setup') # Redirect to profile setup
        
        # Ensure the user has an amor108_member object and is assigned to a pool
        if not hasattr(request.user, 'amor108_member') or not request.user.amor108_profile.membership_pool:
            messages.info(request, "You need to join a pool to access contribution features.")
            return redirect('pools:pool_dashboard') # Redirect to pool selection
            
        return super().dispatch(request, *args, **kwargs)

@login_required
def make_contribution(request):
    user = request.user
    user_profile = user.amor108_profile
    member = user.amor108_member # Assuming Member exists and links to user

    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            if not user_profile.membership_pool:
                messages.error(request, "You must be part of a pool to make contributions.")
                return redirect('contributions:dashboard')

            pool = user_profile.membership_pool
            amount = form.cleaned_data['amount']
            contribution_date = timezone.now().date() # Actual date of contribution

            # Determine expected_date based on current date and pool frequency
            expected_date_for_period = get_next_expected_contribution_date(user_profile, reference_date=contribution_date)
            
            # Find the most recent unverified contribution for this expected_date (if any)
            existing_unverified_contribution = Contribution.objects.filter(
                member=member,
                expected_date=expected_date_for_period,
                is_verified=False
            ).first()

            if existing_unverified_contribution:
                messages.info(request, f"You already have a pending contribution for {expected_date_for_period}. Please wait for verification.")
                return redirect('contributions:dashboard')


            # Get 'Pending' status, create if not exists
            pending_status, created = ContributionStatus.objects.get_or_create(name='Pending', defaults={'description': 'Contribution is awaiting verification.'})

            contribution = Contribution.objects.create(
                member=member,
                amount=amount,
                date=contribution_date,
                expected_date=expected_date_for_period,
                due_date=expected_date_for_period, # For now, due_date is same as expected_date
                status=pending_status,
                transaction_code=f"STK-{uuid.uuid4().hex[:10].upper()}",
                payment_method='MPESA',
                is_verified=False
            )
            messages.success(request, f"Contribution of Ksh {amount} initiated. Transaction: {contribution.transaction_code}. Awaiting verification.")
            return redirect('contributions:dashboard')
    else:
        # Pre-fill amount with expected contribution
        initial_data = {}
        if user_profile and user_profile.membership_pool:
            initial_data['amount'] = user_profile.membership_pool.contribution_amount
        form = ContributionForm(initial=initial_data)
    return render(request, 'contributions/make_contribution.html', {'form': form})

# Helper function for contribution summary
def calculate_contribution_summary(user):
    summary = {
        'total_contributions': Decimal('0.00'),
        'expected_contribution_amount': Decimal('0.00'),
        'expected_contribution_frequency': 'N/A',
        'missed_late_contributions_count': 0,
        'all_contributions': [],
        'contribution_history_clean': True,
    }

    if not hasattr(user, 'amor108_profile'):
        return summary
    
    user_profile = user.amor108_profile
    if not hasattr(user, 'amor108_member'): # Check if member object exists
        return summary
    member = user.amor108_member

    if not user_profile.membership_pool:
        return summary

    pool = user_profile.membership_pool
    
    summary['expected_contribution_amount'] = pool.contribution_amount
    summary['expected_contribution_frequency'] = pool.get_contribution_frequency_display()
    
    # Get all verified contributions for this member
    verified_status, _ = ContributionStatus.objects.get_or_create(name='Verified', defaults={'description': 'Contribution has been verified.'})
    all_verified_contributions = Contribution.objects.filter(
        member=member, 
        is_verified=True, 
        status=verified_status
    ).order_by('expected_date', 'date') # Order by expected date first

    # Get all contributions (verified and unverified) for display in history
    all_contributions_for_history = Contribution.objects.filter(member=member).order_by('-date')
    summary['all_contributions'] = all_contributions_for_history
    
    summary['total_contributions'] = all_verified_contributions.aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')

    # Robust logic for missed/late contributions
    missed_count = 0
    clean_history = True
    
    if member.date_joined_pool:
        today = timezone.now().date()
        current_expected_date = member.date_joined_pool # Start from the join date as the first expected date
        
        while current_expected_date <= today:
            # For monthly contributions, if join date is 15th, then all 15ths of subsequent months are expected dates
            # For daily, every day is an expected date
            
            # Adjust current_expected_date based on frequency to match upcoming expected dates
            if pool.contribution_frequency == 'MONTHLY':
                # Find the next monthly expected date from current_expected_date
                # If member joined on 15th, and current_expected_date is 10th of next month,
                # next expected should be 15th of next month.
                
                # Use get_next_expected_contribution_date to find the next expected date relative to member.date_joined_pool
                expected_date_for_period = get_next_expected_contribution_date(user_profile, reference_date=current_expected_date)
                if not expected_date_for_period: # Should not happen if pool is set
                    break

                # Adjust to make sure we're not checking against an expected date too far in the past
                # The primary logic for missed counts should check up to (today's date)
                if expected_date_for_period > today:
                    break # Stop if we are looking for expected dates in the future

                # Check if a verified contribution exists for this expected_date_for_period
                # within a grace period
                found_contribution = all_verified_contributions.filter(
                    Q(expected_date=expected_date_for_period) | # Ideally matched by expected_date
                    Q(date__gte=expected_date_for_period) # Or made around the expected time
                ).exists()
                
                if not found_contribution:
                    missed_count += 1
                    clean_history = False
                
                current_expected_date += relativedelta(months=1) # Move to next month for iteration
                
                # Make sure current_expected_date stays on the same day of the month as joined, if possible
                if current_expected_date.day != member.date_joined_pool.day:
                    current_expected_date = date(current_expected_date.year, current_expected_date.month, min(member.date_joined_pool.day, (current_expected_date + relativedelta(months=1, days=-1)).day))


            elif pool.contribution_frequency == 'DAILY':
                # Check for daily contributions:
                # Need to verify if there was a contribution for each day between join_date and today
                # This is more complex and would ideally involve looking for contributions on specific dates
                # For now, let's keep the simple count-based logic if too complex to refactor fully here
                pass # Revert to simple count for daily for now if logic is too complex
            
            else: # If not monthly or daily, break
                break

        # Re-evaluate daily logic based on expected dates
        if pool.contribution_frequency == 'DAILY':
            current_expected_day = member.date_joined_pool
            while current_expected_day <= today:
                found_contribution = all_verified_contributions.filter(
                    Q(expected_date=current_expected_day) | # Ideally matched by expected_date
                    Q(date=current_expected_day) # Or made on the exact day
                ).exists()
                if not found_contribution:
                    missed_count += 1
                    clean_history = False
                current_expected_day += timedelta(days=1)
                
    summary['missed_late_contributions_count'] = missed_count
    summary['contribution_history_clean'] = clean_history
    
    # Update user_profile.has_clean_contribution_history and has_missed_contributions
    # These fields are used in pool eligibility
    user_profile.has_clean_contribution_history = clean_history
    user_profile.has_missed_contributions = not clean_history # Inverse of clean history
    user_profile.save(update_fields=['has_clean_contribution_history', 'has_missed_contributions'])

    return summary

class ContributionDashboardView(Amor108MemberRequiredMixin, TemplateView):
    template_name = 'amor108/dashboard_contributions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        summary = calculate_contribution_summary(user)
        
        context.update(summary) # Add all summary items to context

        # Add form for making new contributions
        user_profile = user.amor108_profile
        initial_amount = user_profile.membership_pool.contribution_amount if user_profile and user_profile.membership_pool else Decimal('0.00')
        context['form'] = ContributionForm(initial={'amount': initial_amount})

        return context

@login_required
def mpesa_callback(request):
    """
    Simulates an M-Pesa callback endpoint.
    In a real scenario, this would receive data from M-Pesa's servers.
    """
    if request.method == 'POST':
        # In a real scenario, parse M-Pesa's JSON/XML payload
        # For simulation, we expect transaction_code and optionally amount in POST data
        transaction_code = request.POST.get('transaction_code')
        amount_received_str = request.POST.get('amount') # Optional, for verification
        amount_received = Decimal(amount_received_str) if amount_received_str else None

        if not transaction_code:
            # Log error, return appropriate response for M-Pesa
            return JsonResponse({'status': 'Failed', 'message': 'Missing transaction_code'}, status=400)

        try:
            contribution = Contribution.objects.get(transaction_code=transaction_code, is_verified=False)
            
            # Additional checks: amount_received == contribution.amount, etc.
            if amount_received and amount_received != contribution.amount:
                # Log a warning or error for amount mismatch
                messages.error(request, f"M-Pesa callback amount mismatch for transaction {transaction_code}.")
                return JsonResponse({'status': 'Failed', 'message': 'Amount mismatch'}, status=400)

            verified_status, _ = ContributionStatus.objects.get_or_create(name='Verified', defaults={'description': 'Contribution has been verified.'})
            
            contribution.is_verified = True
            contribution.status = verified_status
            contribution.save()

            # Update user's clean contribution history status
            # Pass the user from the contribution's member
            calculate_contribution_summary(contribution.member.user) # Recalculate and update profile

            messages.success(request, f"Contribution {transaction_code} successfully verified.")
            return JsonResponse({'status': 'Success', 'message': 'Callback processed'})

        except Contribution.DoesNotExist:
            # Log error: transaction_code not found or already verified
            messages.error(request, f"Contribution with transaction code {transaction_code} not found or already verified.")
            return JsonResponse({'status': 'Failed', 'message': 'Contribution not found or already verified'}, status=404)
        except Exception as e:
            # Log other errors
            messages.error(request, f"An error occurred during M-Pesa callback processing: {e}")
            return JsonResponse({'status': 'Failed', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'Failed', 'message': 'Invalid request method'}, status=405)
