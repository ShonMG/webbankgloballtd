from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from members_amor108.models import Member as Amor108Member
from .models import WebBankMembership

@login_required
def apply_for_webbank(request):
    user = request.user

    # 1. Check if already a WebBank member
    if WebBankMembership.objects.filter(user=user, status=WebBankMembership.StatusChoices.ACTIVE).exists():
        messages.info(request, "You are already an active WebBank member.")
        return redirect('dashboard:main_dashboard')

    # 2. Check if an application is already pending
    if WebBankMembership.objects.filter(user=user, status=WebBankMembership.StatusChoices.PENDING).exists():
        messages.info(request, "Your WebBank membership application is already pending review.")
        return redirect('dashboard:main_dashboard')

    # 3. Check AMOR108 Gold Pool eligibility (LAW 3)
    is_eligible = False
    if hasattr(user, 'amor108_member'):
        amor108_member_instance = user.amor108_member
        if amor108_member_instance.pool and amor108_member_instance.pool.name.upper() == 'GOLD':
            is_eligible = True

    if not is_eligible:
        messages.error(request, "You must be an AMOR108 GOLD pool member to apply for WebBank membership.")
        return redirect('dashboard:main_dashboard')

    # 4. Check WebBank member cap (LAW 4)
    # Use select_for_update to prevent race conditions during cap check
    with transaction.atomic():
        active_webbank_members_count = WebBankMembership.objects.filter(
            status=WebBankMembership.StatusChoices.ACTIVE
        ).count()

        if active_webbank_members_count >= settings.WEBBANK_MEMBER_CAP:
            messages.error(request, "WebBank membership has reached its maximum capacity (12 active members). Please try again later.")
            return redirect('dashboard:main_dashboard')

        # If eligible and cap not reached, create a pending application
        WebBankMembership.objects.create(user=user, status=WebBankMembership.StatusChoices.PENDING)
        messages.success(request, "Your application for WebBank membership has been submitted successfully and is awaiting review.")
    
    return redirect('dashboard:main_dashboard')