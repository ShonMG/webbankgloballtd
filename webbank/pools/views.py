from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, View, TemplateView
from django.contrib.auth.mixins import AccessMixin
from django.contrib import messages # Import messages for user feedback
from django.db.models import Q # Import Q object for complex queries
from .models import Pool # Resolution removed from here
from governance.models import Resolution # Import Resolution model from governance app
from .forms import PoolForm
from accounts_amor108.models import Amor108Profile # Import Amor108Profile

class Amor108MemberRequiredMixin(AccessMixin):
    """Verify that the current user is an AMOR108 member or staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Allow staff/admins to view pool pages
        if request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'amor108_profile'):
            messages.error(request, "You need to complete your Amor108 profile to access pool features.")
            return redirect('amor108:profile_setup') # Assuming a profile setup URL
        return super().dispatch(request, *args, **kwargs)

class PoolListView(Amor108MemberRequiredMixin, ListView):
    model = Pool
    template_name = 'pools/pool_list.html'
    context_object_name = 'pools'

class PoolDetailView(Amor108MemberRequiredMixin, DetailView):
    model = Pool
    template_name = 'pools/pool_detail.html'
    context_object_name = 'pool'

class PoolCreateView(Amor108MemberRequiredMixin, CreateView):
    model = Pool
    form_class = PoolForm
    template_name = 'pools/pool_form.html'
    success_url = reverse_lazy('pools:pool_list')

    def form_valid(self, form):
        form.instance.manager = self.request.user
        return super().form_valid(form)

class PoolJoinView(Amor108MemberRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pool = get_object_or_404(Pool, pk=kwargs['pk'])
        user_profile = request.user.amor108_profile

        # Check eligibility before joining
        is_eligible, reason = user_profile.check_pool_entry_eligibility()
        if not is_eligible:
            messages.error(request, f"Cannot join pool: {reason}")
            return redirect('pools:pool_detail', pk=pool.pk)

        if not pool.is_locked and request.user not in pool.members.all():
            pool.members.add(request.user)
            user_profile.membership_pool = pool # Assign pool to user's profile
            user_profile.save()
            pool.check_and_lock_pool()
            messages.success(request, f"Successfully joined {pool.name}!")
        elif request.user in pool.members.all():
            messages.info(request, f"You are already a member of {pool.name}.")
        else:
            messages.warning(request, f"{pool.name} is currently locked.")
        return redirect('pools:pool_detail', pk=pool.pk)

class PoolDashboardView(Amor108MemberRequiredMixin, TemplateView):
    template_name = 'amor108/dashboard_pools.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_profile = user.amor108_profile

        # Current Pool Participation
        context['member_pool'] = user_profile.membership_pool

        # Pool Upgrade Eligibility
        context['can_upgrade'] = False # Placeholder
        context['next_pool_requirements'] = None # Placeholder
        if context['member_pool']:
            # Example: Determine eligibility for next tier based on current pool's contribution or user's history
            is_eligible_for_upgrade, upgrade_reason = user_profile.check_pool_entry_eligibility()
            if is_eligible_for_upgrade:
                # Find the next higher tier pool, if any
                current_pool_amount = context['member_pool'].contribution_amount
                next_tier_pool = Pool.objects.filter(
                    Q(contribution_amount__gt=current_pool_amount) &
                    Q(is_active=True) &
                    Q(is_locked=False)
                ).order_by('contribution_amount').first()

                if next_tier_pool:
                    context['can_upgrade'] = True
                    context['next_pool_requirements'] = next_tier_pool
        else: # If user is not in any pool, they can join the lowest tier
            is_eligible_to_join_any, reason = user_profile.check_pool_entry_eligibility()
            if is_eligible_to_join_any:
                lowest_tier_pool = Pool.objects.filter(is_active=True, is_locked=False).order_by('contribution_amount').first()
                if lowest_tier_pool:
                    context['can_upgrade'] = True # Can 'upgrade' into the first pool
                    context['next_pool_requirements'] = lowest_tier_pool # Present lowest as 'next'

        # All Available Pools
        context['all_pools'] = Pool.objects.filter(is_active=True).order_by('contribution_amount')

        # Downgrade Status (from Amor108Profile)
        context['voting_rights_revoked'] = user_profile.voting_rights_revoked
        context['loan_visibility_reduced'] = user_profile.loan_visibility_reduced
        context['reduced_credit_power'] = user_profile.reduced_credit_power

        # Pool Governance Resolutions
        # Resolutions visible to all, and those specific to the user's current pool
        context['resolutions'] = Resolution.objects.filter(
            Q(visible_to_all=True) | Q(pool=context['member_pool'])
        ).order_by('-creation_date')
        
        # Add user's vote status for each resolution
        for resolution in context['resolutions']:
            resolution.user_has_voted = resolution.votes.filter(voter=user).exists()
            resolution.can_vote, resolution.can_vote_reason = resolution.can_user_vote(user)


        return context

class UpgradePoolView(Amor108MemberRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        user_profile = user.amor108_profile
        target_pool = get_object_or_404(Pool, pk=kwargs['pk'])

        # Check eligibility for upgrade
        is_eligible, reason = user_profile.check_pool_entry_eligibility()
        if not is_eligible:
            messages.error(request, f"Cannot upgrade pool: {reason}")
            return redirect('pools:pool_dashboard')
        
        # Check if the target pool is actually an upgrade
        if user_profile.membership_pool and target_pool.contribution_amount <= user_profile.membership_pool.contribution_amount:
            messages.error(request, "The selected pool is not a higher tier than your current pool.")
            return redirect('pools:pool_dashboard')

        # Ensure the target pool is active and not locked
        if not target_pool.is_active or target_pool.is_locked:
            messages.error(request, f"Cannot upgrade to {target_pool.name}: Pool is either inactive or locked.")
            return redirect('pools:pool_dashboard')
            
        # Perform the upgrade
        # Remove user from current pool if any
        if user_profile.membership_pool:
            user_profile.membership_pool.members.remove(user)
            user_profile.membership_pool.check_and_lock_pool() # Re-check lock status of old pool

        target_pool.members.add(user)
        user_profile.membership_pool = target_pool
        user_profile.save()
        target_pool.check_and_lock_pool() # Re-check lock status of new pool

        messages.success(request, f"Successfully upgraded to {target_pool.name}!")
        return redirect('pools:pool_dashboard')
