from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import AccessMixin
from django.db.models import Q, Sum
from django.urls import reverse_lazy
from decimal import Decimal
from django.utils import timezone

from .models import AuditLog
from accounts_amor108.models import Amor108Profile
from pools.models import Pool # For pool performance/rule changes related to pools
from governance.models import Resolution # For governance rule changes
from contributions.models import Contribution # Added for dynamic financial summaries
from profits.models import MemberProfit # Added for dynamic financial summaries
from loans.models import Loan # Added for dynamic financial summaries
from documents.models import Document # Added for dynamic pool performance reports

class Amor108MemberRequiredMixin(AccessMixin):
    """Verify that the current user is an AMOR108 member or staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.is_staff: # Staff can view everything without full profile
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'amor108_profile'):
            messages.error(request, "You need to complete your Amor108 profile to access transparency features.")
            return redirect('accounts_amor108:profile_setup')
            
        return super().dispatch(request, *args, **kwargs)

class TransparencyDashboardView(Amor108MemberRequiredMixin, TemplateView):
    template_name = 'amor108/dashboard_transparency.html' # This view still renders an amor108 template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        member_profile = None
        if hasattr(user, 'amor108_member'): # Use amor108_member for consistency with other views
            member_profile = user.amor108_member

        end_date = timezone.now()
        start_date_12_months_ago = end_date - timezone.timedelta(days=365)

        # Dynamic Financial Summaries
        total_contributions_last_12_months = Contribution.objects.filter(
            member__user=user,
            date__range=(start_date_12_months_ago, end_date)
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

        total_profit_distributions_last_cycle = MemberProfit.objects.filter(
            member__user=user,
            created_at__range=(start_date_12_months_ago, end_date),
            action__in=['WITHDRAWN', 'REINVESTED'] # Only consider distributed/reinvested profits
        ).aggregate(Sum('net_profit'))['net_profit__sum'] or Decimal('0.00')

        total_loans_disbursed_last_12_months = Loan.objects.filter(
            Q(member=user) | Q(amor108_member__user=user),
            status='disbursed',
            disbursement_date__range=(start_date_12_months_ago, end_date)
        ).aggregate(Sum('amount_approved'))['amount_approved__sum'] or Decimal('0.00')
        
        context['financial_summaries'] = [
            {'title': 'Total Contributions (Last 12 Months)', 'value': f'Ksh {total_contributions_last_12_months:,.2f}'},
            {'title': 'Total Profit Distributions (Last Year)', 'value': f'Ksh {total_profit_distributions_last_cycle:,.2f}'},
            {'title': 'Total Loans Disbursed (Last 12 Months)', 'value': f'Ksh {total_loans_disbursed_last_12_months:,.2f}'},
        ]

        # Dynamic Pool Performance Reports
        context['pool_performance_reports'] = []
        if member_profile and member_profile.pool:
            pool_reports_for_member = Document.objects.filter(
                Q(owner=user) | Q(owner__isnull=True), # Documents owned by user or public
                # Assuming Document model has a foreign key to Pool, or a way to link
                # For now, a simple text search if no direct link
                Q(title__icontains=member_profile.pool.name) | Q(description__icontains=member_profile.pool.name),
                Q(title__icontains='performance report') | Q(description__icontains='performance report')
            ).order_by('-uploaded_at')[:5]

            for report in pool_reports_for_member:
                context['pool_performance_reports'].append(
                    {'pool_name': member_profile.pool.name, 'title': report.title, 'details_link': report.file.url if report.file else '#'}
                )
        if not context['pool_performance_reports'] and member_profile and member_profile.pool: # Fallback if no specific reports for the pool
             context['pool_performance_reports'].append({'pool_name': member_profile.pool.name, 'title': 'No specific performance reports found for your pool.', 'details_link': '#'})
        elif not context['pool_performance_reports']: # General fallback
            context['pool_performance_reports'].append({'pool_name': 'N/A', 'title': 'No specific performance reports found.', 'details_link': '#'})


        # Rule Changes (From Governance Resolutions)
        # Show binding resolutions that changed rules, if any
        context['rule_changes_logs'] = Resolution.objects.filter(
            Q(vote_type='BINDING') & (Q(visible_to_all=True) | Q(pool=member_profile.pool if member_profile else None))
        ).order_by('-creation_date')[:5] # Last 5 binding rule changes/resolutions

        # Admin Actions (Sanitized Audit Logs)
        # Filter for actions performed by admins/directors, excluding sensitive details
        context['admin_action_logs'] = AuditLog.objects.filter(
            Q(user__user_type__in=['director', 'admin', 'founder']) | Q(action__startswith='ADMIN_')
        ).exclude(action='LOGIN').order_by('-timestamp')[:10] # Last 10 admin actions

        # All audit logs for the current user
        context['my_audit_logs'] = AuditLog.objects.filter(user=user).order_by('-timestamp')[:10]


        return context