from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import AccessMixin
from django.db.models import Q
from django.urls import reverse_lazy

from .models import Resolution, Vote
from accounts_amor108.models import Amor108Profile
from members_amor108.models import Member as Amor108Member
from shares.models import Share # For voting power calculation

class Amor108MemberRequiredMixin(AccessMixin):
    """Verify that the current user is an AMOR108 member or staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'amor108_profile'):
            messages.error(request, "You need to complete your Amor108 profile to access governance features.")
            return redirect('accounts_amor108:profile_setup')
        
        if not hasattr(request.user, 'amor108_member'):
            messages.info(request, "You need a member record to access governance features.")
            return redirect('pools:pool_dashboard') # Assuming user needs to be a member
            
        return super().dispatch(request, *args, **kwargs)

# Helper function to calculate voting power
def get_voting_power(user):
    # Default voting power
    voting_power = 0

    if not hasattr(user, 'amor108_member'):
        return voting_power

    member = user.amor108_member
    
    # Voting power based on shares held
    try:
        share_account = Share.objects.get(member=member)
        voting_power += share_account.units # Each share unit contributes to voting power
    except Share.DoesNotExist:
        pass # No shares, no voting power from shares

    # Voting power based on pool status (e.g., Gold Tier members might get bonus power)
    if hasattr(user, 'amor108_profile') and user.amor108_profile.membership_pool:
        if user.amor108_profile.membership_pool.name == 'Gold Tier':
            voting_power += 10 # Example: Gold Tier members get 10 bonus voting points

    return voting_power

class VotingDashboardView(Amor108MemberRequiredMixin, TemplateView):
    template_name = 'amor108/dashboard_voting.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        member = user.amor108_member # Get the Amor108Member instance
        
        # Calculate voting power
        context['voting_power'] = get_voting_power(user)

        # Active resolutions (open for voting)
        active_resolutions = Resolution.objects.filter(is_active=True, deadline__gt=timezone.now()).order_by('-creation_date')
        
        # Filter resolutions visible to all or specific to user's pool
        if member.pool:
            active_resolutions = active_resolutions.filter(Q(visible_to_all=True) | Q(pool=member.pool))
        else:
            active_resolutions = active_resolutions.filter(visible_to_all=True)
        
        # Add user-specific voting info to each active resolution
        for res in active_resolutions:
            res.user_has_voted = res.votes.filter(voter=user).exists()
            res.can_vote, res.can_vote_reason = res.can_user_vote(user)

        context['active_resolutions'] = active_resolutions

        # Voting history (past resolutions, including user's vote if cast)
        voting_history_resolutions = Resolution.objects.filter(Q(is_active=False) | Q(deadline__lte=timezone.now())).order_by('-deadline', '-creation_date')
        
        # For voting history, we need to associate user's past votes
        user_votes_map = {v.resolution_id: v for v in Vote.objects.filter(voter=user)}
        
        for res in voting_history_resolutions:
            res.user_vote = user_votes_map.get(res.id) # Will be a Vote object or None
            res.outcome = "Approved" if res.yes_votes > res.no_votes else ("Rejected" if res.no_votes > res.yes_votes else "Tie")
            
        context['voting_history'] = voting_history_resolutions

        return context

class VoteResolutionView(Amor108MemberRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        resolution = get_object_or_404(Resolution, pk=kwargs['pk'])
        user = request.user
        vote_choice_str = request.POST.get('vote_choice') # Expect 'yes' or 'no' from form
        vote_choice = vote_choice_str == 'yes'

        success, message = resolution.record_vote(user, vote_choice)

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
        return redirect('governance:dashboard') # Redirect back to the governance dashboard
