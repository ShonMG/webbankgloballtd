from django.contrib import admin
from django.contrib.auth import get_user_model
from datetime import timedelta # Import timedelta

from .models import MembershipStatus, Member, ExitRequest

User = get_user_model()

@admin.register(MembershipStatus)
class MembershipStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'pool', 'status', 'is_suspended', 'date_joined_pool')
    list_filter = ('pool', 'status', 'is_suspended')
    search_fields = ('user__username', 'user__email', 'next_of_kin_names')
    raw_id_fields = ('user',)
    actions = ['suspend_members', 'activate_members']

    fieldsets = (
        (None, {
            'fields': ('user', 'pool', 'status', 'is_suspended', 'suspension_reason', 'share_ownership_details')
        }),
        ('Next of Kin Information', {
            'fields': (
                'next_of_kin_names',
                'next_of_kin_mobile_no',
                'next_of_kin_email_address',
                'next_of_kin_identification_passport_no',
                'next_of_kin_nationality'
            ),
            'classes': ('collapse',)
        }),
    )

    @admin.action(description='Suspend selected members')
    def suspend_members(self, request, queryset):
        # Set status to 'Suspended' and is_suspended to True
        suspended_status = MembershipStatus.objects.get(name='Suspended')
        queryset.update(is_suspended=True, status=suspended_status)
        self.message_user(request, f"{queryset.count()} members successfully suspended.")

    @admin.action(description='Activate selected members')
    def activate_members(self, request, queryset):
        # Set status to 'Active' and is_suspended to False
        active_status = MembershipStatus.objects.get(name='Active')
        queryset.update(is_suspended=False, status=active_status)
        self.message_user(request, f"{queryset.count()} members successfully activated.")

@admin.register(ExitRequest)
class ExitRequestAdmin(admin.ModelAdmin):
    list_display = ('member', 'request_date', 'effective_exit_date', 'is_approved', 'processed_by')
    list_filter = ('is_approved', 'request_date')
    search_fields = ('member__user__username', 'reason')
    raw_id_fields = ('member', 'processed_by')
    actions = ['approve_exit_requests', 'reject_exit_requests']

    @admin.action(description='Approve selected exit requests')
    def approve_exit_requests(self, request, queryset):
        # Update is_approved and set effective_exit_date (e.g., 30 days from now)
        # Also change member status to 'Exited' after effective_exit_date
        exited_status = MembershipStatus.objects.get(name='Exited')
        for exit_request in queryset:
            exit_request.is_approved = True
            # For simplicity, setting effective_exit_date as request_date + 30 days
            # A real implementation might use a task queue for this.
            exit_request.effective_exit_date = exit_request.request_date + timedelta(days=30) 
            exit_request.processed_by = request.user
            exit_request.save()
            # Mark member as exited after the effective date
            # exit_request.member.status = exited_status # This would be triggered by a cron job or similar
            # exit_request.member.save()
        self.message_user(request, f"{queryset.count()} exit requests approved.")

    @admin.action(description='Reject selected exit requests')
    def reject_exit_requests(self, request, queryset):
        queryset.update(is_approved=False, processed_by=request.user) # Optionally clear effective_exit_date
        self.message_user(request, f"{queryset.count()} exit requests rejected.")