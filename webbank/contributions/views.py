from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ContributionForm
from .models import Contribution
from members_amor108.models import Member as Amor108Member
from django.utils import timezone
from decimal import Decimal
from django.db import models

@login_required
def make_contribution(request):
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.member = request.user.amor108_member
            contribution.save()
            return redirect('amor108:dashboard')
    else:
        form = ContributionForm()
    return render(request, 'contributions/make_contribution.html', {'form': form})

def get_total_contributions(member):
    return Contribution.objects.filter(member=member).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')

def get_contribution_summary(member):
    # This is a placeholder for more complex logic
    # In a real application, you would calculate expected contributions,
    # consistency, and missed/late contributions based on the member's pool
    # and join date.
    total_contributions = get_total_contributions(member)
    all_contributions = Contribution.objects.filter(member=member).order_by('-date')
    
    summary = {
        'total_contributions': total_contributions,
        'expected_contribution_amount': member.pool.contribution_amount if member.pool else 0,
        'expected_contribution_frequency': member.pool.get_contribution_frequency_display() if member.pool else 'N/A',
        'total_contributions_to_date': total_contributions,
        'contribution_consistency': '100%', # Placeholder
        'missed_late_contributions_count': 0, # Placeholder
        'all_contributions': all_contributions,
    }
    return summary
