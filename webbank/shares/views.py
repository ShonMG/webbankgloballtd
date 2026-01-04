from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from decimal import Decimal
import random
import string
from django.utils import timezone # Import timezone
from .models import Share, ShareTransaction, Dividend, ShareConfig
from .forms import SharePurchaseForm, ShareGoalForm, DividendForm # Import DividendForm
from accounts.models import User
from members_amor108.models import Member as Amor108Member # Import Amor108Member
from loans.models import Loan # Import Loan model
from django.core import serializers # Import serializers
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def shares_dashboard(request):
    user = request.user

    # If user is admin, show a list of all shares
    if user.is_staff:
        all_shares = Share.objects.all().select_related('member__user')
        return render(request, 'shares/all_shares_admin.html', {'shares': all_shares, 'user_type': user.user_type})

    # If regular user, check if they are an AMOR108 member
    if not hasattr(user, 'amor108_member'):
        return render(request, 'shares/not_amor108_member.html')

    amor108_member = user.amor108_member
    share, created = Share.objects.get_or_create(member=amor108_member)

    # Initialize forms
    purchase_form = SharePurchaseForm()
    share_goal_form = ShareGoalForm(instance=share)

    if request.method == 'POST':
        if 'purchase_submit' in request.POST:
            purchase_form = SharePurchaseForm(request.POST)
            if purchase_form.is_valid():
                units = purchase_form.cleaned_data['units']
                unit_price = ShareConfig.objects.first().current_unit_price if ShareConfig.objects.exists() else Decimal('100.00')
                total_amount = units * unit_price
                
                share.units += units
                share.save() # This will update total_value
                
                ShareTransaction.objects.create(
                    member=amor108_member,
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
        
        elif 'set_goal_submit' in request.POST:
            share_goal_form = ShareGoalForm(request.POST, instance=share)
            if share_goal_form.is_valid():
                share_goal_form.save()
                messages.success(request, 'Monthly share target updated successfully!')
                return redirect('shares:shares_dashboard')
            else:
                messages.error(request, 'Error updating monthly share target. Please check your input.')

    purchase_history = ShareTransaction.objects.filter(
        member=amor108_member, 
        transaction_type='purchase'
    ).order_by('-transaction_date')
    
    overall_target = Decimal('200000.00')
    total_share_cap = Decimal('2000000.00')

    # Calculate monthly progress
    now = timezone.now()
    monthly_contributed_value = ShareTransaction.objects.filter(
        member=amor108_member,
        transaction_type='purchase',
        transaction_date__year=now.year,
        transaction_date__month=now.month
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    monthly_progress_percentage = 0
    if share.monthly_share_target and share.monthly_share_target > 0:
        monthly_progress_percentage = (monthly_contributed_value / share.monthly_share_target) * 100

    # Determine if shares are locked (LAW 7 & 8)
    shares_are_locked = False
    active_loan_statuses = ['active', 'disbursed']

    if Loan.objects.filter(Q(amor108_member=amor108_member) | Q(guarantors=amor108_member), status__in=active_loan_statuses).exists():
        shares_are_locked = True

    context = {
        'share': share,
        'total_units': share.units,
        'total_value': share.total_value,
        'purchase_history': purchase_history,
        'purchase_form': purchase_form,
        'share_goal_form': share_goal_form,
        'user_type': user.user_type,
        'overall_target': overall_target,
        'total_share_cap': total_share_cap,
        'shares_are_locked': shares_are_locked,
        'monthly_contributed_value': monthly_contributed_value,
        'monthly_progress_percentage': monthly_progress_percentage,
    }
    
    return render(request, 'shares/shares.html', context)


@login_required
def transactions_history(request):
    user = request.user

    if user.is_staff:
        # Admins should see all transactions or be redirected
        return redirect('shares:shares_dashboard')

    if not hasattr(user, 'amor108_member'):
        return render(request, 'shares/not_amor108_member.html')

    amor108_member = user.amor108_member
    all_transactions = ShareTransaction.objects.filter(member=amor108_member).order_by('-transaction_date')
    
    context = {
        'all_transactions': all_transactions,
        'user_type': user.user_type,
    }
    return render(request, 'shares/transactions_history.html', context)

@login_required
def view_performance(request):
    user = request.user

    if user.is_staff:
        return redirect('shares:shares_dashboard')

    if not hasattr(user, 'amor108_member'):
        return render(request, 'shares/not_amor108_member.html')
        
    amor108_member = user.amor108_member
    transactions = ShareTransaction.objects.filter(member=amor108_member).order_by('transaction_date')
    
    transactions_json = serializers.serialize('json', transactions)

    context = {
        'transactions': transactions,
        'transactions_json': transactions_json,
        'user_type': user.user_type,
    }
    return render(request, 'shares/view_performance.html', context)

@staff_member_required
def declare_dividend(request):
    if request.method == 'POST':
        form = DividendForm(request.POST)
        if form.is_valid():
            dividend = form.save(commit=False)
            
            if not dividend.tax_rate:
                share_config = ShareConfig.objects.first()
                if share_config:
                    dividend.tax_rate = share_config.dividend_tax_rate
            
            dividend.save()
            messages.success(request, 'Dividend declared successfully!')
            return redirect('shares:dividend_list')
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
    
    dividend.is_approved = True
    dividend.save()
    
    shares = Share.objects.filter(units__gt=0)
    
    total_distributed_amount = Decimal('0.00')
    total_tax_deducted = Decimal('0.00')

    for share in shares:
        eligible_units = share.units
        
        gross_dividend = eligible_units * share.unit_price * dividend.dividend_rate
        tax_amount = gross_dividend * dividend.tax_rate
        net_dividend = gross_dividend - tax_amount
        
        if net_dividend > 0:
            ShareTransaction.objects.create(
                member=share.member,
                transaction_type='dividend',
                units=0,
                unit_price=Decimal('0.00'),
                total_amount=net_dividend,
                description=f'Dividend distribution (Gross: {gross_dividend:.2f}, Tax: {tax_amount:.2f})',
                reference_number=f"DIV{dividend.id}_{share.member.id}_{''.join(random.choices(string.digits, k=4))}",
                dividend=dividend
            )
            total_distributed_amount += net_dividend
            total_tax_deducted += tax_amount
            
    messages.success(request, f'Dividend declared on {dividend.declaration_date} has been approved and distributed.')
    messages.info(request, f'Total Net Dividend Distributed: KES {total_distributed_amount:.2f}. Total Tax Deducted: KES {total_tax_deducted:.2f}.')
    
    return redirect('shares:dividend_list')

@login_required
def buy_shares(request):
    # This is a placeholder view. Actual implementation would involve a form for amount, payment processing, etc.
    context = {
        'active_page': 'buy_shares',
    }
    return render(request, 'shares/buy_shares.html', context)

@login_required
def withdraw_shares(request):
    # This is a placeholder view. Actual implementation would involve a form for amount, validation, etc.
    context = {
        'active_page': 'withdraw_shares',
    }
    return render(request, 'shares/withdraw_shares.html', context)
