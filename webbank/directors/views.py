from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.utils import timezone
from accounts.models import User
from loans.models import Loan, LoanApprovalLog
from shares.models import Share

def is_director(user):
    return user.user_type == 'director'

@login_required
@user_passes_test(is_director)
def directors_dashboard(request):
    # Director-specific statistics
    total_members = User.objects.filter(user_type='member').count()
    active_loans = Loan.objects.filter(status__in=['active', 'disbursed']).count()
    total_shares = Share.objects.aggregate(total=Sum('total_value'))['total'] or 0
    pending_applications = Loan.objects.filter(approval_stage='pending_director').count()
    
    # Pending decisions
    pending_loans = Loan.objects.filter(approval_stage='pending_director')[:5]
    
    context = {
        'total_members': total_members,
        'active_loans': active_loans,
        'total_shares': total_shares,
        'pending_applications': pending_applications,
        'pending_loans': pending_loans,
    }
    
    return render(request, 'directors/directors.html', context)

@login_required
@user_passes_test(is_director)
def loan_approval_list(request):
    if request.method == 'POST':
        selected_loans_ids = request.POST.getlist('selected_loans')
        bulk_action = request.POST.get('bulk_action')
        
        loans_to_update = Loan.objects.filter(id__in=selected_loans_ids, approval_stage='pending_director')
        
        for loan in loans_to_update:
            # Log the action
            LoanApprovalLog.objects.create(
                loan=loan,
                approver=request.user,
                action=bulk_action,
                comments=f"Bulk {bulk_action} by director.",
            )

            if bulk_action == 'approved':
                loan.approval_stage = 'approved' # Final approval
                loan.director_approved_by = request.user
                loan.director_approval_date = timezone.now()
                loan.status = 'approved' # Update loan status to indicate final approval
                messages.success(request, f"Loan {loan.loan_id} bulk approved by director.")
            elif bulk_action == 'rejected':
                loan.approval_stage = 'rejected'
                loan.status = 'rejected'
                messages.error(request, f"Loan {loan.loan_id} bulk rejected by director.")
            loan.save()
        
        return redirect('directors:loan_approval_list')

    loans_pending_approval = Loan.objects.filter(approval_stage='pending_director').order_by('application_date')
    context = {
        'loans': loans_pending_approval,
        'approval_stage_name': 'Director Approval'
    }
    return render(request, 'directors/loan_approval_list.html', context)

@login_required
@user_passes_test(is_director)
def loan_approval_detail(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, approval_stage='pending_director')
    
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

        if action == 'approved':
            loan.approval_stage = 'approved' # Final approval
            loan.director_approved_by = request.user
            loan.director_approval_date = timezone.now()
            loan.status = 'approved' # Update loan status to indicate final approval
            messages.success(request, f"Loan {loan.loan_id} finally approved by director.")
        elif action == 'rejected':
            loan.approval_stage = 'rejected'
            loan.status = 'rejected'
            messages.error(request, f"Loan {loan.loan_id} rejected by director.")
        
        loan.save()
        return redirect('directors:loan_approval_list')
    
    context = {
        'loan': loan,
        'approval_logs': loan.approval_logs.all().order_by('-timestamp')
    }
    return render(request, 'directors/loan_approval_detail.html', context)