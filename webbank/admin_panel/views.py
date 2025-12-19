from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone
from accounts.models import User
from loans.models import Loan, LoanApprovalLog, LoanType
from shares.models import Share, ShareConfig, ShareTransaction
from admin_panel.models import SaccoConfiguration, AuditLog # Import AuditLog
from admin_panel.forms import LoanTypeForm, ShareConfigForm, SaccoConfigurationForm, UserAdminForm, NotificationSettingForm, NotificationTemplateForm
from notifications.models import NotificationSetting, NotificationTemplate
from profiles.models import Profile
from django.contrib import messages
from accounts.decorators import admin_required, founder_required
from decimal import Decimal # Import Decimal for monetary values
from django.http import HttpResponse # Import HttpResponse
import csv # Import csv module
from members_amor108.models import Member as Amor108Member

@login_required
@admin_required
def pending_amor108_members(request):
    pending_members = Amor108Member.objects.filter(status__name='pending')
    context = {
        'members': pending_members,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/pending_amor108_members.html', context)

@login_required
@admin_required
def approve_amor108_member(request, member_id):
    member = get_object_or_404(Amor108Member, id=member_id)
    member.status = 'approved'
    member.user.is_active = True
    member.save()
    member.user.save()
    messages.success(request, f'Amor108 member {member.user.username} has been approved.')
    return redirect('admin_panel:pending_amor108_members')

@login_required
@admin_required
def reject_amor108_member(request, member_id):
    member = get_object_or_404(Amor108Member, id=member_id)
    user = member.user
    member.status = 'rejected'
    member.save()
    user.delete()
    messages.error(request, f'Amor108 member {user.username} has been rejected and their account deleted.')
    return redirect('admin_panel:pending_amor108_members')


def export_to_csv(filename, headers, data):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    return response

@login_required
@admin_required
def pending_members(request):
    pending_profiles = Profile.objects.filter(approved=False)
    context = {
        'profiles': pending_profiles,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/pending_members.html', context)

@login_required
@admin_required
def approve_member(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    profile.approved = True
    profile.save()
    messages.success(request, f'Member {profile.user.username} has been approved.')
    return redirect('admin_panel:pending_members')

@login_required
@admin_required
def reject_member(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    user = profile.user
    profile.delete()
    user.delete()
    messages.error(request, f'Member {user.username} has been rejected and their account deleted.')
    return redirect('admin_panel:pending_members')


@login_required
@admin_required
def admin_dashboard(request):
    # Admin statistics
    total_members = User.objects.filter(user_type='member').count()
    active_loans_count = Loan.objects.filter(status__in=['active', 'disbursed']).count()
    total_shares_value = Share.objects.aggregate(total=Sum('total_value'))['total'] or 0

    # Financial Oversight Calculations
    total_disbursed_loans_amount = Loan.objects.filter(status='disbursed').aggregate(total=Sum('amount_approved'))['total'] or 0
    total_sacco_assets = total_shares_value + total_disbursed_loans_amount # Simplified asset calculation

    total_loans = Loan.objects.count()
    defaulted_loans_count = Loan.objects.filter(status='defaulted').count()
    loan_default_rate = (defaulted_loans_count / total_loans * 100) if total_loans > 0 else 0

    # Placeholder for real-time dividend calculations (e.g., total interest earned)
    # A more complex dividend calculation would depend on profit, operational costs, etc.
    total_interest_earned_calculated = Decimal('0.00')
    relevant_loans = Loan.objects.filter(status__in=['active', 'completed', 'disbursed'])
    for loan in relevant_loans:
        # Simple interest calculation: Principal * Rate * Time (in years)
        # Assuming loan.interest_rate is annual percentage, term_months is total months
        if loan.amount_approved is not None and loan.interest_rate is not None and loan.term_months is not None:
            # Convert annual percentage to monthly decimal rate
            # interest_rate is a DecimalField, so direct division is fine
            monthly_rate = (loan.interest_rate / Decimal('100')) / Decimal('12')
            # Total interest for the loan (Principal * Rate * Time)
            # The 'time' here is in months, so monthly_rate * term_months
            loan_interest = loan.amount_approved * monthly_rate * loan.term_months
            total_interest_earned_calculated += loan_interest

    # Use the calculated value
    total_interest_earned = total_interest_earned_calculated

    pending_applications = Loan.objects.filter(approval_stage='pending_manager').count()
    
    # Recent loan applications
    recent_loans = Loan.objects.select_related('member', 'loan_type').order_by('-application_date')[:5]
    
    context = {
        'total_members': total_members,
        'active_loans': active_loans_count,
        'total_shares': total_shares_value,
        'pending_applications': pending_applications,
        'recent_loans': recent_loans,
        'total_sacco_assets': total_sacco_assets,
        'loan_default_rate': loan_default_rate,
        'total_interest_earned': total_interest_earned,
        'user_type': request.user.user_type,
    }
    
    return render(request, 'admin_panel/admin_dashboard.html', context)

@login_required
@admin_required
def loan_approval_list(request):
    if request.method == 'POST':
        selected_loans_ids = request.POST.getlist('selected_loans')
        bulk_action = request.POST.get('bulk_action')
        
        loans_to_update = Loan.objects.filter(id__in=selected_loans_ids, approval_stage='pending_manager')
        
        for loan in loans_to_update:
            # Log the action
            LoanApprovalLog.objects.create(
                loan=loan,
                approver=request.user,
                action=bulk_action,
                comments=f"Bulk {bulk_action} by manager.",
            )
            # Audit Log for loan approval
            AuditLog.objects.create(
                user=request.user,
                action=f"Bulk loan {bulk_action} by manager",
                details=f"Loan ID: {loan.pk}, Loan type: {loan.loan_type.name}",
                ip_address=request.META.get('REMOTE_ADDR'),
                object_repr=str(loan),
                object_id=loan.pk
            )

            if bulk_action == 'approved':
                loan.approval_stage = 'pending_director'
                loan.manager_approved_by = request.user
                loan.manager_approval_date = timezone.now()
                loan.status = 'approved_manager'
                messages.success(request, f"Loan {loan.loan_id} bulk approved by manager and forwarded for director approval.")
            elif bulk_action == 'rejected':
                loan.approval_stage = 'rejected'
                loan.status = 'rejected'
                messages.error(request, f"Loan {loan.loan_id} bulk rejected by manager.")
            loan.save()
        
        return redirect('admin_panel:loan_approval_list')

    loans_pending_approval = Loan.objects.filter(approval_stage='pending_manager').order_by('application_date')
    context = {
        'loans': loans_pending_approval,
        'approval_stage_name': 'Manager Approval',
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/loan_approval_list.html', context)

@login_required
@admin_required
def loan_approval_detail(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, approval_stage='pending_manager')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        
        # Log the action
        LoanApprovalLog.objects.create(
            loan=loan,
            approver=request.user,
            action=action,
            comments=comments,
        )
        # Audit Log for loan approval
        AuditLog.objects.create(
            user=request.user,
            action=f"{action.capitalize()} loan",
            details=f"Loan ID: {loan.pk}, Comments: {comments}",
            ip_address=request.META.get('REMOTE_ADDR'),
            object_repr=str(loan),
            object_id=loan.pk
        )

        if action == 'approved':
            loan.approval_stage = 'pending_director' # Forward to director
            loan.manager_approved_by = request.user
            loan.manager_approval_date = timezone.now()
            loan.status = 'approved_manager' # Update loan status to indicate manager approval
            messages.success(request, f"Loan {loan.loan_id} approved by manager and forwarded for director approval.")
        elif action == 'rejected':
            loan.approval_stage = 'rejected'
            loan.status = 'rejected'
            messages.error(request, f"Loan {loan.loan_id} rejected by manager.")
        
        loan.save()
        return redirect('admin_panel:loan_approval_list')
    
    context = {
        'loan': loan,
        'approval_logs': loan.approval_logs.all().order_by('-timestamp'),
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/loan_approval_detail.html', context)

@login_required
@admin_required
def loan_config_panel(request):
    loantypes = LoanType.objects.all().order_by('name')
    context = {
        'loantypes': loantypes,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/loan_config_panel.html', context)

@login_required
@admin_required
def loan_type_form(request, pk=None):
    if pk:
        loantype = get_object_or_404(LoanType, pk=pk)
    else:
        loantype = None

    if request.method == 'POST':
        form = LoanTypeForm(request.POST, instance=loantype)
        if form.is_valid():
            form.save()
            messages.success(request, "Loan Type saved successfully.")
            return redirect('admin_panel:loan_config_panel')
    else:
        form = LoanTypeForm(instance=loantype)
    
    context = {
        'form': form,
        'loantype': loantype,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/loan_type_form.html', context)

@login_required
@admin_required
def share_config_panel(request):
    share_config, created = ShareConfig.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = ShareConfigForm(request.POST, instance=share_config)
        if form.is_valid():
            form.save()
            messages.success(request, "Share Configuration saved successfully.")
            return redirect('admin_panel:share_config_panel')
    else:
        form = ShareConfigForm(instance=share_config)
    
    context = {
        'form': form,
        'share_config': share_config,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/share_config_panel.html', context)

@login_required
@admin_required
def system_config_panel(request):
    sacco_config, created = SaccoConfiguration.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = SaccoConfigurationForm(request.POST, instance=sacco_config)
        if form.is_valid():
            form.save()
            messages.success(request, "System Configuration saved successfully.")
            return redirect('admin_panel:system_config_panel')
    else:
        form = SaccoConfigurationForm(instance=sacco_config)
    
    context = {
        'form': form,
        'sacco_config': sacco_config,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/system_config_panel.html', context)

@login_required
@founder_required
def founder_dashboard(request):
    # Founder statistics
    total_members = User.objects.filter(user_type='member').count()
    total_directors = User.objects.filter(user_type='director').count()
    total_admins = User.objects.filter(user_type='admin').count()
    total_guarantors = User.objects.filter(user_type='guarantor').count()
    total_loans = Loan.objects.count()
    total_shares_value = Share.objects.aggregate(total=Sum('total_value'))['total'] or 0

    context = {
        'total_members': total_members,
        'total_directors': total_directors,
        'total_admins': total_admins,
        'total_guarantors': total_guarantors,
        'total_loans': total_loans,
        'total_shares_value': total_shares_value,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/founder_dashboard.html', context)


# User Management Views
@login_required
@admin_required
def user_list(request):
    users = User.objects.all().order_by('username')
    user_type_filter = request.GET.get('user_type')
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)

    context = {
        'users': users,
        'user_types': User.USER_TYPES,
        'selected_user_type': user_type_filter,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/user_list.html', context)

@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UserAdminForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(User.objects.make_random_password()) # Set a random password
            user.save()
            # Audit Log
            AuditLog.objects.create(
                user=request.user,
                action=f"Created user '{user.username}'",
                details=f"User ID: {user.pk}, Type: {user.user_type}",
                ip_address=request.META.get('REMOTE_ADDR'),
                object_repr=str(user),
                object_id=user.pk
            )
            messages.success(request, f"User {user.username} created successfully with a random password. Please communicate it to the user.")
            return redirect('admin_panel:user_list')
    else:
        form = UserAdminForm()
    
    context = {
        'form': form,
        'title': 'Create New User',
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/user_form.html', context)

@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=user)
        if form.is_valid():
            new_user_type = form.cleaned_data['user_type']
            
            # Check qualification if trying to set user_type to 'director'
            if new_user_type == 'director':
                qualifies, message = check_board_member_qualification(user)
                if not qualifies:
                    messages.error(request, f"Cannot set user as Director: {message}")
                    return render(request, 'admin_panel/user_form.html', {
                        'form': form,
                        'user': user,
                        'title': f'Edit User: {user.username}',
                        'user_type': request.user.user_type,
                    })
            
            form.save()
            # Audit Log
            AuditLog.objects.create(
                user=request.user,
                action=f"Edited user '{user.username}'",
                details=f"User ID: {user.pk}, Changes: {form.changed_data}",
                ip_address=request.META.get('REMOTE_ADDR'),
                object_repr=str(user),
                object_id=user.pk
            )
            messages.success(request, f"User {user.username} updated successfully.")
            return redirect('admin_panel:user_list')
    else:
        form = UserAdminForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Edit User: {user.username}',
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/user_form.html', context)

@login_required
@admin_required
def user_deactivate(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status_message = "deactivated" if not user.is_active else "activated"
        # Audit Log
        AuditLog.objects.create(
            user=request.user,
            action=f"{status_message.capitalize()} user '{user.username}'",
            details=f"User ID: {user.pk}",
            ip_address=request.META.get('REMOTE_ADDR'),
            object_repr=str(user),
            object_id=user.pk
        )
        messages.success(request, f"User {user.username} has been {status_message}.")
        return redirect('admin_panel:user_list')
    
    context = {
        'user': user,
        'action': 'deactivate' if user.is_active else 'activate',
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/user_confirm_action.html', context)

@login_required
@admin_required
def user_reset_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        new_password = User.objects.make_random_password()
        user.set_password(new_password)
        user.save()
        # Audit Log
        AuditLog.objects.create(
            user=request.user,
            action=f"Reset password for user '{user.username}'",
            details=f"User ID: {user.pk}",
            ip_address=request.META.get('REMOTE_ADDR'),
            object_repr=str(user),
            object_id=user.pk
        )
        messages.success(request, f"Password for {user.username} has been reset to: {new_password}. Please ensure to communicate this securely to the user.")
        return redirect('admin_panel:user_list')
    
    context = {
        'user': user,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/user_confirm_reset_password.html', context)


# Notification Management Views
@login_required
@admin_required
def notification_settings_panel(request):
    notification_settings, created = NotificationSetting.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = NotificationSettingForm(request.POST, instance=notification_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification settings updated successfully.")
            return redirect('admin_panel:notification_settings_panel')
    else:
        form = NotificationSettingForm(instance=notification_settings)
    
    context = {
        'form': form,
        'notification_settings': notification_settings,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/notification_settings_panel.html', context)

@login_required
@admin_required
def notification_template_list(request):
    templates = NotificationTemplate.objects.all().order_by('notification_type')
    
    context = {
        'templates': templates,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/notification_template_list.html', context)

@login_required
@admin_required
def notification_template_edit(request, pk):
    template = get_object_or_404(NotificationTemplate, pk=pk)
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f"Notification template for {template.get_notification_type_display()} updated successfully.")
            return redirect('admin_panel:notification_template_list')
    else:
        form = NotificationTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin_panel/notification_template_form.html', context)


# Reporting Views
@login_required
@admin_required
def reporting_dashboard(request):
    context = {
        'user_type': request.user.user_type,
        'title': 'Reporting Dashboard',
    }
    return render(request, 'admin_panel/reporting_dashboard.html', context)

@login_required
@admin_required
def loan_performance_report(request):
    # Filtering options
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    loan_type_id = request.GET.get('loan_type')
    loan_status = request.GET.get('status')

    loans = Loan.objects.all()

    if start_date_str:
        loans = loans.filter(application_date__gte=start_date_str)
    if end_date_str:
        loans = loans.filter(application_date__lte=end_date_str)
    if loan_type_id:
        loans = loans.filter(loan_type__id=loan_type_id)
    if loan_status:
        loans = loans.filter(status=loan_status)

    total_loans_count = loans.count()
    total_amount_applied = loans.aggregate(total=Sum('amount_applied'))['total'] or Decimal('0.00')
    total_amount_approved = loans.aggregate(total=Sum('amount_approved'))['total'] or Decimal('0.00')
    
    active_loans = loans.filter(status='active').count()
    completed_loans = loans.filter(status='completed').count()
    defaulted_loans = loans.filter(status='defaulted').count()
    
    # Calculate average interest rate on filtered loans
    avg_interest_rate = loans.aggregate(avg_rate=Avg('loan_type__interest_rate'))['avg_rate'] or Decimal('0.00')
    
    # Loans by status for potential chart
    loans_by_status = loans.values('status').annotate(count=Count('id'))

    # Top performing loan types (by total approved amount)
    top_loan_types = loans.values('loan_type__name').annotate(
        total_approved=Sum('amount_approved')
    ).order_by('-total_approved')[:5]

    all_loan_types = LoanType.objects.all()
    all_loan_statuses = Loan.LOAN_STATUS # Corrected to LOAN_STATUS

    context = {
        'total_loans_count': total_loans_count,
        'total_amount_applied': total_amount_applied,
        'total_amount_approved': total_amount_approved,
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'defaulted_loans': defaulted_loans,
        'avg_interest_rate': avg_interest_rate,
        'loans_by_status': list(loans_by_status), # Convert to list for JSON serialization if needed
        'top_loan_types': list(top_loan_types),
        'all_loan_types': all_loan_types,
        'all_loan_statuses': all_loan_statuses,
        'user_type': request.user.user_type,
        'title': 'Loan Performance Report',

        # For retaining filter values
        'selected_start_date': start_date_str,
        'selected_end_date': end_date_str,
        'selected_loan_type': loan_type_id,
        'selected_status': loan_status,
    }

    # Export functionality for Loan Performance Report
    if request.GET.get('export') == 'csv':
        response_data = []
        response_data.append(['Loan Performance Report'])
        response_data.append(['Filter Criteria:'])
        response_data.append(['Start Date', start_date_str])
        response_data.append(['End Date', end_date_str])
        response_data.append(['Loan Type ID', loan_type_id])
        response_data.append(['Loan Status', loan_status])
        response_data.append(['', ''])

        response_data.append(['Metric', 'Value'])
        response_data.append(['Total Loans', total_loans_count])
        response_data.append(['Total Amount Applied', total_amount_applied])
        response_data.append(['Total Amount Approved', total_amount_approved])
        response_data.append(['Active Loans', active_loans])
        response_data.append(['Completed Loans', completed_loans])
        response_data.append(['Defaulted Loans', defaulted_loans])
        response_data.append(['Average Interest Rate', avg_interest_rate])
        response_data.append(['', ''])

        response_data.append(['Loans by Status', 'Count'])
        for entry in loans_by_status:
            response_data.append([entry['status'], entry['count']])
        response_data.append(['', ''])

        response_data.append(['Top Loan Types (by Approved Amount)', 'Total Approved'])
        for entry in top_loan_types:
            response_data.append([entry['loan_type__name'], entry['total_approved']])
        
        headers = ['Description', 'Value']
        return export_to_csv('loan_performance_report', headers, response_data)

    return render(request, 'admin_panel/loan_performance_report.html', context)

@login_required
@admin_required
def member_growth_report(request):
    selected_year = request.GET.get('year', str(timezone.now().year))
    
    members_by_month_data = []
    if selected_year:
        members_by_month_query = User.objects.filter(
            user_type='member',
            date_joined__year=selected_year
        ).annotate(
            month=ExtractMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        # Initialize counts for all 12 months to 0
        monthly_counts = {i: 0 for i in range(1, 13)}
        for entry in members_by_month_query:
            monthly_counts[entry['month']] = entry['count']
        
        # Format for Chart.js
        for month_num in range(1, 13):
            members_by_month_data.append({
                'month': datetime(1, month_num, 1).strftime('%b'), # Month abbreviation
                'count': monthly_counts[month_num]
            })

    # Get a list of available years for filtering
    available_years = User.objects.filter(user_type='member', date_joined__isnull=False).annotate(
        year=ExtractYear('date_joined')
    ).values_list('year', flat=True).distinct().order_by('year')
    
    context = {
        'members_by_month_data': members_by_month_data,
        'selected_year': selected_year,
        'available_years': available_years,
        'user_type': request.user.user_type,
        'title': 'Member Growth Report',
    }
    
    # Export functionality for Member Growth Report
    if request.GET.get('export') == 'csv':
        response_data = []
        response_data.append(['Member Growth Report'])
        response_data.append(['Selected Year', selected_year])
        response_data.append(['', ''])

        response_data.append(['Month', 'New Members'])
        for entry in members_by_month_data:
            response_data.append([entry['month'], entry['count']])
        
        headers = ['Month', 'New Members']
        return export_to_csv('member_growth_report', headers, response_data)

    return render(request, 'admin_panel/member_growth_report.html', context)

@login_required
@admin_required
def share_value_trends_report(request):
    selected_year = request.GET.get('year', str(timezone.now().year))

    share_value_data = []
    if selected_year:
        # Use ShareTransaction model to get share value trends based on transaction_date.
        # This provides an accurate trend of share purchases over time.
        
        shares_by_month_query = ShareTransaction.objects.filter(
            transaction_date__year=selected_year,
            transaction_type='purchase'  # Consider only purchases for value trend
        ).annotate(
            month=ExtractMonth('transaction_date')
        ).values('month').annotate(
            total_value=Sum('total_amount')
        ).order_by('month')

        # Initialize values for all 12 months to 0
        monthly_values = {i: Decimal('0.00') for i in range(1, 13)}
        for entry in shares_by_month_query:
            monthly_values[entry['month']] = entry['total_value']
        
        # Format for Chart.js
        from datetime import datetime
        for month_num in range(1, 13):
            share_value_data.append({
                'month': datetime(1, month_num, 1).strftime('%b'),
                'value': monthly_values[month_num]
            })

    # Get a list of available years for filtering from ShareTransaction
    available_years = ShareTransaction.objects.filter(transaction_date__isnull=False).annotate(
        year=ExtractYear('transaction_date')
    ).values_list('year', flat=True).distinct().order_by('-year')

    context = {
        'share_value_data': share_value_data,
        'selected_year': selected_year,
        'available_years': available_years,
        'user_type': request.user.user_type,
        'title': 'Share Value Trends Report',
    }

    # Export functionality for Share Value Trends Report
    if request.GET.get('export') == 'csv':
        response_data = []
        response_data.append(['Share Value Trends Report'])
        response_data.append(['Selected Year', selected_year])
        response_data.append(['', ''])

        response_data.append(['Month', 'Total Share Value'])
        for entry in share_value_data:
            response_data.append([entry['month'], entry['value']])
        
        headers = ['Month', 'Total Share Value']
        return export_to_csv('share_value_trends_report', headers, response_data)

    return render(request, 'admin_panel/share_value_trends_report.html', context)


# Audit & Compliance Views
@login_required
@admin_required
def audit_log_list(request):
    audit_logs = AuditLog.objects.all().order_by('-action_time')
    context = {
        'audit_logs': audit_logs,
        'user_type': request.user.user_type,
        'title': 'Audit Log',
    }
    return render(request, 'admin_panel/audit_log_list.html', context)

from datetime import datetime, timedelta

@login_required
@admin_required
def financial_statements_report(request):
    # Get date range for Income Statement
    today = timezone.now().date()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        # Default to current month for income statement
        start_date = today.replace(day=1)
        end_date = today

    # --- Balance Sheet (Snapshot as of end_date) ---
    # Assets
    cash_balance = Decimal('1500000.00')  # Simulated initial cash
    
    # Loans Receivable: Total disbursed loans minus total repayments
    loans_disbursed = Loan.objects.filter(disbursement_date__lte=end_date, status__in=['active', 'completed', 'disbursed']).aggregate(total=Sum('amount_approved'))['total'] or Decimal('0.00')
    loans_repaid = Loan.objects.filter(loan_repayments__payment_date__lte=end_date, status__in=['active', 'completed', 'disbursed']).aggregate(total=Sum('loan_repayments__amount'))['total'] or Decimal('0.00')
    loans_receivable = loans_disbursed - loans_repaid

    investments_shares = ShareTransaction.objects.filter(transaction_date__lte=end_date).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    total_assets = cash_balance + loans_receivable + investments_shares

    # Liabilities
    member_deposits = Decimal('1000000.00') # Simulated member deposits
    loans_payable = Decimal('0.00') # Simulated, assuming no external Sacco loans

    total_liabilities = member_deposits + loans_payable

    # Equity
    # Calculate share capital by summing all share purchase transactions up to the end_date.
    share_capital = ShareTransaction.objects.filter(
        transaction_date__lte=end_date,
        transaction_type='purchase'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Retained Earnings (simplified: accumulated net income)
    # This requires summing up net income over all past periods, which is complex.
    # For now, let's derive it from Assets - Liabilities - Share Capital
    retained_earnings = total_assets - total_liabilities - share_capital
    
    total_equity = share_capital + retained_earnings

    # --- Income Statement (For the period start_date to end_date) ---
    # Revenue
    interest_income_loans = Loan.objects.filter(
        disbursement_date__gte=start_date,
        disbursement_date__lte=end_date
    ).aggregate(total=Sum('loan_type__interest_rate') * Sum('amount_approved') / 100)['total'] or Decimal('0.00')
    # This is a very rough calculation for interest income.
    # A proper calculation would involve specific interest payments over the period.
    # For simplicity, calculate 10% of disbursed amount in the period as interest
    interest_income_loans = Loan.objects.filter(
        disbursement_date__range=(start_date, end_date)
    ).aggregate(total=Sum('amount_approved') * Decimal('0.10'))['total'] or Decimal('0.00') # Simplified to 10% of disbursed amount in period
    
    other_income = Decimal('10000.00') # Simulated other income for the period

    total_revenue = interest_income_loans + other_income

    # Expenses
    operating_expenses = Decimal('50000.00') # Simulated operating expenses for the period
    interest_expense = Decimal('0.00') # Simulated, assuming no interest paid on deposits for simplicity

    total_expenses = operating_expenses + interest_expense

    net_income = total_revenue - total_expenses

    # Export functionality
    if request.GET.get('export') == 'csv':
        response_data = []
        # Balance Sheet Data
        response_data.append(['Balance Sheet as of', end_date.strftime('%Y-%m-%d')])
        response_data.append(['ASSETS', ''])
        response_data.append(['Cash Balance', cash_balance])
        response_data.append(['Loans Receivable', loans_receivable])
        response_data.append(['Investments (Shares)', investments_shares])
        response_data.append(['Total Assets', total_assets])
        response_data.append(['', ''])

        response_data.append(['LIABILITIES', ''])
        response_data.append(['Member Deposits', member_deposits])
        response_data.append(['Loans Payable', loans_payable])
        response_data.append(['Total Liabilities', total_liabilities])
        response_data.append(['', ''])

        response_data.append(['EQUITY', ''])
        response_data.append(['Share Capital', share_capital])
        response_data.append(['Retained Earnings', retained_earnings])
        response_data.append(['Total Equity', total_equity])
        response_data.append(['', ''])
        response_data.append(['----------------------------------', '----------------------------------'])
        response_data.append(['', ''])

        # Income Statement Data
        response_data.append(['Income Statement for the period', f'{start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'])
        response_data.append(['REVENUE', ''])
        response_data.append(['Interest Income (Loans)', interest_income_loans])
        response_data.append(['Other Income', other_income])
        response_data.append(['Total Revenue', total_revenue])
        response_data.append(['', ''])

        response_data.append(['EXPENSES', ''])
        response_data.append(['Operating Expenses', operating_expenses])
        response_data.append(['Interest Expense', interest_expense])
        response_data.append(['Total Expenses', total_expenses])
        response_data.append(['', ''])

        response_data.append(['NET INCOME', net_income])
        
        headers = ['Description', 'Amount']
        return export_to_csv('financial_statements_report', headers, response_data)

    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'user_type': request.user.user_type,
        'title': 'Financial Statements Report',
        
        # Balance Sheet
        'cash_balance': cash_balance,
        'loans_receivable': loans_receivable,
        'investments_shares': investments_shares,
        'total_assets': total_assets,
        
        'member_deposits': member_deposits,
        'loans_payable': loans_payable,
        'total_liabilities': total_liabilities,
        
        'share_capital': share_capital,
        'retained_earnings': retained_earnings,
        'total_equity': total_equity,

        # Income Statement
        'interest_income_loans': interest_income_loans,
        'other_income': other_income,
        'total_revenue': total_revenue,
        
        'operating_expenses': operating_expenses,
        'interest_expense': interest_expense,
        'total_expenses': total_expenses,
        
        'net_income': net_income,
    }
    return render(request, 'admin_panel/financial_statements_report.html', context)