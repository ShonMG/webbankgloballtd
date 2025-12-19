from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Role, PermissionProfile, Amor108Profile, LoginHistory

User = get_user_model()

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

@admin.register(PermissionProfile)
class PermissionProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

@admin.register(Amor108Profile)
class Amor108ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'membership_pool', 'is_approved')
    list_filter = ('role', 'membership_pool', 'is_approved')
    search_fields = ('user__username', 'user__email', 'next_of_kin_names')
    raw_id_fields = ('user',) # Useful for ForeignKey to User when many users
    actions = ['approve_members', 'unapprove_members'] # Custom admin actions

    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'membership_pool', 'is_approved')
        }),
        ('Next of Kin Information', {
            'fields': (
                'next_of_kin_names',
                'next_of_kin_mobile_no',
                'next_of_kin_email_address',
                'next_of_kin_identification_passport_no',
                'next_of_kin_nationality'
            ),
            'classes': ('collapse',) # Collapse this section by default
        }),
    )

    # Custom admin action to approve selected members
    @admin.action(description='Approve selected members')
    def approve_members(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} members successfully approved.")

    # Custom admin action to unapprove selected members
    @admin.action(description='Unapprove selected members')
    def unapprove_members(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} members successfully unapproved.")

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address', 'user_agent')
    list_filter = ('login_time',)
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'login_time', 'ip_address', 'user_agent') # Make fields read-only
    date_hierarchy = 'login_time' # Add a date drilldown navigation