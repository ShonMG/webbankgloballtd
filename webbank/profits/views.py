from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import MemberProfit, ProfitCycle
from members_amor108.models import Member as Amor108Member
from shares.models import Share, ShareTransaction
from decimal import Decimal
import random
import string

@login_required
def member_profits_list(request):
    member = get_object_or_404(Amor108Member, user=request.user)
    member_profits = MemberProfit.objects.filter(member=member).order_by('-profit_cycle__end_date')
    
    context = {
        'member_profits': member_profits
    }
    return render(request, 'profits/member_profits_list.html', context)

@login_required
def withdraw_profit(request, pk):
    member_profit = get_object_or_404(MemberProfit, pk=pk, member__user=request.user)

    if member_profit.action != 'PENDING':
        messages.warning(request, "This profit has already been actioned.")
        return redirect('profits:member_profits_list')

    if request.method == 'POST':
        with transaction.atomic():
            member_profit.action = 'WITHDRAWN'
            member_profit.action_date = timezone.now()
            member_profit.save()

            # Here you would typically integrate with a payment gateway or internal transfer system
            # For now, we just mark it as withdrawn.
            messages.success(request, f"Successfully withdrew {member_profit.net_profit} from {member_profit.profit_cycle.name}.")
            return redirect('profits:member_profits_list')
    
    context = {
        'member_profit': member_profit
    }
    return render(request, 'profits/withdraw_profit.html', context)

@login_required
def reinvest_profit(request, pk):
    member_profit = get_object_or_404(MemberProfit, pk=pk, member__user=request.user)

    if member_profit.action != 'PENDING':
        messages.warning(request, "This profit has already been actioned.")
        return redirect('profits:member_profits_list')

    if request.method == 'POST':
        with transaction.atomic():
            # Get or create the member's share account
            share_account, created = Share.objects.get_or_create(member=member_profit.member)
            
            # Calculate units to add (simplified: assume current unit price)
            # In a real system, you might use the unit price at the time of reinvestment
            current_unit_price = share_account.unit_price # Or from ShareConfig
            
            if current_unit_price <= 0:
                messages.error(request, "Cannot reinvest, share unit price is zero or negative.")
                return redirect('profits:member_profits_list')

            units_to_add = (member_profit.net_profit / current_unit_price).quantize(Decimal('1'))
            
            if units_to_add < 1:
                messages.warning(request, "Net profit is too low to purchase a full share unit for reinvestment.")
                # Optionally, handle partial units or leave as pending
                return redirect('profits:member_profits_list')

            # Update share account
            share_account.units += units_to_add
            share_account.save() # This updates total_value automatically

            # Create a ShareTransaction record for reinvestment
            ShareTransaction.objects.create(
                member=member_profit.member,
                transaction_type='reinvestment', # Add 'reinvestment' to ShareTransaction.TRANSACTION_TYPES
                units=units_to_add,
                unit_price=current_unit_price,
                total_amount=member_profit.net_profit,
                description=f'Reinvestment of profit from {member_profit.profit_cycle.name}',
                reference_number=f"REINV{member_profit.id}_{share_account.member.id}_{''.join(random.choices(string.digits, k=4))}"
            )

            member_profit.action = 'REINVESTED'
            member_profit.action_date = timezone.now()
            member_profit.reinvestment_transaction = share_account # Link to the share account that was updated
            member_profit.save()

            messages.success(request, f"Successfully reinvested {member_profit.net_profit} into {units_to_add} shares.")
            return redirect('profits:member_profits_list')
    
    context = {
        'member_profit': member_profit
    }
    return render(request, 'profits/reinvest_profit.html', context)
