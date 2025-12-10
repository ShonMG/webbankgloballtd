from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
import random
import string
from .models import Share, ShareTransaction, Dividend, ShareConfig
from .forms import SharePurchaseForm, ShareGoalForm, DividendForm # Import DividendForm
from accounts.models import User
from django.core import serializers # Import serializers
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def shares_dashboard(request):
    user = request.user
    
    # Get or create the user's single share object
    share, created = Share.objects.get_or_create(member=user) # Use get_or_create directly here

    # Initialize forms
    purchase_form = SharePurchaseForm()
    share_goal_form = ShareGoalForm(instance=share) # Pre-fill with existing target

    if request.method == 'POST':
        if 'purchase_submit' in request.POST: # Check which form was submitted
            purchase_form = SharePurchaseForm(request.POST)
            if purchase_form.is_valid():
                units = purchase_form.cleaned_data['units']
                unit_price = Decimal('100.00') # Assuming unit price is always 100.00 as per models.py default
                total_amount = units * unit_price
                
                share.units += units
                share.save() # This will update total_value
                
                # Create transaction record
                ShareTransaction.objects.create(
                    member=user,
                    transaction_type='purchase',
                    units=units,
                    unit_price=unit_price,
                    total_amount=total_amount,
                    description=f'Purchase of {units} shares',
                    reference_number=f"TXN{''.join(random.choices(string.digits, k=8))}"
                )
                
                messages.info(request, f"STK Push initiated for KES {total_amount} to purchase {units} shares. Please approve the transaction on your phone.")
                messages.success(request, f'Successfully purchased {units} shares!')
                return redirect('shares:shares_dashboard')
        
        elif 'set_goal_submit' in request.POST: # Check which form was submitted
            share_goal_form = ShareGoalForm(request.POST, instance=share)
            if share_goal_form.is_valid():
                share_goal_form.save()
                messages.success(request, 'Monthly share target updated successfully!')
                return redirect('shares:shares_dashboard')
            else:
                messages.error(request, 'Error updating monthly share target. Please check your input.')


    purchase_history = ShareTransaction.objects.filter(
        member=user, 
        transaction_type='purchase'
    ).order_by('-transaction_date')
    
    # Define targets as Decimal to avoid float issues in templates
    overall_target = Decimal('200000.00')
    total_share_cap = Decimal('2000000.00')

    context = {
        'share': share,
        'total_units': share.units,
        'total_value': share.total_value,
        'purchase_history': purchase_history,
        'purchase_form': purchase_form, # Renamed for clarity
        'share_goal_form': share_goal_form, # New form
        'user_type': user.user_type,
        'overall_target': overall_target, # Pass to context
        'total_share_cap': total_share_cap, # Pass to context
    }
    
    return render(request, 'shares/shares.html', context)


@login_required
def transactions_history(request):
    user = request.user
    # Fetch all share transactions for the user, ordered by date
    all_transactions = ShareTransaction.objects.filter(member=user).order_by('-transaction_date')
    
    context = {
        'all_transactions': all_transactions,
        'user_type': user.user_type,
    }
    return render(request, 'shares/transactions_history.html', context)

@login_required
def view_performance(request):
    user = request.user
    transactions = ShareTransaction.objects.filter(member=user).order_by('transaction_date')
    
    # Serialize QuerySet to JSON
    transactions_json = serializers.serialize('json', transactions)

    context = {
        'transactions': transactions, # Keep for table display
        'transactions_json': transactions_json, # Pass JSON for Chart.js
        'user_type': user.user_type,
    }
    return render(request, 'shares/view_performance.html', context)

@staff_member_required
def declare_dividend(request):
    if request.method == 'POST':
        form = DividendForm(request.POST)
        if form.is_valid():
            dividend = form.save(commit=False)
            
            # Optionally, fetch default tax rate from ShareConfig if not provided in form
            if not dividend.tax_rate:
                share_config = ShareConfig.objects.first()
                if share_config:
                    dividend.tax_rate = share_config.dividend_tax_rate
            
            dividend.save()
            messages.success(request, 'Dividend declared successfully!')
            return redirect('shares:dividend_list') # Redirect to a list of dividends
        else:
            messages.error(request, 'Error declaring dividend. Please check your input.')
    else:
        form = DividendForm()
    
    context = {
        'form': form,
        'user_type': request.user.user_type,
    }
    return render(request, 'shares/declare_dividend.html', context)

@staff_member_required
def dividend_list(request):
    dividends = Dividend.objects.all().order_by('-declaration_date')
    
    context = {
        'dividends': dividends,
        'user_type': request.user.user_type,
    }
    return render(request, 'shares/dividend_list.html', context)

@staff_member_required
def approve_dividend(request, dividend_id):
    try:
        dividend = Dividend.objects.get(id=dividend_id)
    except Dividend.DoesNotExist:
        messages.error(request, 'Dividend not found.')
        return redirect('shares:dividend_list')
    
    if dividend.is_approved:
        messages.warning(request, 'This dividend has already been approved and distributed.')
        return redirect('shares:dividend_list')
    
    # Mark dividend as approved
    dividend.is_approved = True
    dividend.save()
    
    # Distribute dividends
    shares = Share.objects.filter(units__gt=0) # Only consider members with shares
    
    total_distributed_amount = Decimal('0.00')
    total_tax_deducted = Decimal('0.00')

    for share in shares:
        # Calculate dividend for each member
        # Only shares held on or before the effective date are eligible
        eligible_units = share.units # Assuming all units are eligible for simplicity for now
        
        gross_dividend = eligible_units * share.unit_price * dividend.dividend_rate
        tax_amount = gross_dividend * dividend.tax_rate
        net_dividend = gross_dividend - tax_amount
        
        if net_dividend > 0:
            # Create a ShareTransaction record for the dividend
            ShareTransaction.objects.create(
                member=share.member,
                transaction_type='dividend',
                units=0, # Dividends are not units
                unit_price=Decimal('0.00'),
                total_amount=net_dividend,
                description=f'Dividend distribution (Gross: {gross_dividend:.2f}, Tax: {tax_amount:.2f})',
                reference_number=f"DIV{dividend.id}_{share.member.id}_{''.join(random.choices(string.digits, k=4))}",
                dividend=dividend # Link to the specific dividend declaration
            )
            total_distributed_amount += net_dividend
            total_tax_deducted += tax_amount
            
            # Optionally, update member's balance or add to their share account
            # For this implementation, we are just recording the transaction.
            # Actual crediting to a bank account would involve another system/model.
            
    messages.success(request, f'Dividend declared on {dividend.declaration_date} has been approved and distributed.')
    messages.info(request, f'Total Net Dividend Distributed: KES {total_distributed_amount:.2f}. Total Tax Deducted: KES {total_tax_deducted:.2f}.')
    
    return redirect('shares:dividend_list')