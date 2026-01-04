from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.views.generic import TemplateView, View # Import TemplateView and View
from django.contrib.auth.mixins import AccessMixin # Import AccessMixin
from django.urls import reverse_lazy # Import reverse_lazy

from .models import MemberProfit, ProfitCycle
from members_amor108.models import Member as Amor108Member
from shares.models import Share, ShareTransaction
from accounts_amor108.models import Amor108Profile # Import Amor108Profile
from .utils import get_profit_summary # Import the utility function
from decimal import Decimal
import random
import string

# Define Amor108MemberRequiredMixin (copied from contributions.views for consistency)
class Amor108MemberRequiredMixin(AccessMixin):
    """Verify that the current user is an AMOR108 member or staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'amor108_profile'):
            messages.error(request, "You need to complete your Amor108 profile to access profit features.")
            return redirect('accounts_amor108:profile_setup')
        if not hasattr(request.user, 'amor108_member'):
            messages.info(request, "You need a member record to access profit features.")
            return redirect('pools:pool_dashboard') # Assuming user needs to be a member
            
        return super().dispatch(request, *args, **kwargs)

class ProfitDashboardView(Amor108MemberRequiredMixin, TemplateView):
    template_name = 'amor108/dashboard_profits.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        summary = get_profit_summary(user)
        
        context.update(summary) # Add all summary items to context
        
        # Add a form for withdrawal if needed, or link to withdrawal view
        # Add a form for reinvestment if needed, or link to reinvestment view
        
        return context

@login_required
def withdraw_profit(request, pk):
    member_profit = get_object_or_404(MemberProfit, pk=pk, member__user=request.user)

    if member_profit.action != 'PENDING':
        messages.warning(request, "This profit has already been actioned.")
        return redirect('profits:dashboard') # Redirect to dashboard

    # Check eligibility using get_profit_summary
    summary = get_profit_summary(request.user)
    if not summary['can_withdraw']:
        messages.error(request, f"Cannot withdraw profits: {', '.join(summary['withdrawal_ineligibility_reasons'])}")
        return redirect('profits:dashboard') # Redirect to dashboard

    if request.method == 'POST':
        with transaction.atomic():
            member_profit.action = 'WITHDRAWN'
            member_profit.action_date = timezone.now()
            member_profit.save()

            # Here you would typically integrate with a payment gateway or internal transfer system
            # For now, we just mark it as withdrawn.
            messages.success(request, f"Successfully withdrew {member_profit.net_profit} from {member_profit.profit_cycle.name}.")
            return redirect('profits:dashboard') # Redirect to dashboard
    
    context = {
        'member_profit': member_profit
    }
    return render(request, 'profits/withdraw_profit.html', context)

@login_required
def reinvest_profit(request, pk):
    member_profit = get_object_or_404(MemberProfit, pk=pk, member__user=request.user)

    if member_profit.action != 'PENDING':
        messages.warning(request, "This profit has already been actioned.")
        return redirect('profits:dashboard') # Redirect to dashboard

    # Check eligibility using get_profit_summary (can_reinvest is usually true if there are pending profits)
    summary = get_profit_summary(request.user)
    if summary['accrued_profits'] <= 0: # Should be caught by previous check, but good to double check
        messages.error(request, "No pending profits to reinvest.")
        return redirect('profits:dashboard') # Redirect to dashboard

    if request.method == 'POST':
        with transaction.atomic():
            # Get or create the member's share account
            share_account, created = Share.objects.get_or_create(member=member_profit.member)
            
            # Calculate units to add (simplified: assume current unit price from ShareConfig)
            from shares.models import ShareConfig # Import ShareConfig here
            share_config = ShareConfig.objects.first()
            current_unit_price = share_config.current_unit_price if share_config else Decimal('100.00') # Default if no config

            if current_unit_price <= 0:
                messages.error(request, "Cannot reinvest, share unit price is zero or negative.")
                return redirect('profits:dashboard') # Redirect to dashboard

            units_to_add = (member_profit.net_profit / current_unit_price).quantize(Decimal('1'))
            
            if units_to_add < 1:
                messages.warning(request, "Net profit is too low to purchase a full share unit for reinvestment.")
                return redirect('profits:dashboard') # Redirect to dashboard

            # Update share account
            share_account.units += units_to_add
            share_account.save()

            # Create a ShareTransaction record for reinvestment
            reinvestment_transaction = ShareTransaction.objects.create(
                member=member_profit.member,
                transaction_type='reinvestment', # Use the new transaction type
                units=units_to_add,
                unit_price=current_unit_price,
                total_amount=member_profit.net_profit,
                description=f'Reinvestment of profit from {member_profit.profit_cycle.name}',
                reference_number=f"REINV{member_profit.id}_{share_account.member.id}_{''.join(random.choices(string.digits, k=4))}",
                # dividend=None # Ensure dividend is not set for reinvestment
            )

            member_profit.action = 'REINVESTED'
            member_profit.action_date = timezone.now()
            member_profit.reinvestment_transaction = reinvestment_transaction # Link to the ShareTransaction
            member_profit.save()

            messages.success(request, f"Successfully reinvested {member_profit.net_profit} into {units_to_add} shares.")
            return redirect('profits:dashboard') # Redirect to dashboard
    
    context = {
        'member_profit': member_profit
    }
    return render(request, 'profits/reinvest_profit.html', context)
