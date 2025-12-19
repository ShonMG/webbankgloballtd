from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Value
from django.db import models # Correct import for models
from django.db.models.functions import Coalesce
from accounts.models import User

def is_admin(user):
    return user.user_type == 'admin'

@login_required
@user_passes_test(is_admin)
def members_dashboard(request):
    members_list = User.objects.filter(user_type='member').annotate(
        total_shares_value=Coalesce(Sum('amor108_member__share_account__total_value'), Value(0), output_field=models.DecimalField())
    ).order_by('-date_joined')
    
    # Statistics
    total_members = members_list.count()
    active_members = members_list.filter(is_active=True).count()
    pending_approval = User.objects.filter(is_verified=False, user_type='member').count()
    directors_count = User.objects.filter(user_type='director').count()
    
    context = {
        'members': members_list,
        'total_members': total_members,
        'active_members': active_members,
        'pending_approval': pending_approval,
        'directors_count': directors_count,
    }
    
    return render(request, 'members/members.html', context)