from django.contrib import admin
from .models import Pool, PoolManagerAssignment

@admin.register(Pool)
class PoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'contribution_amount', 'contribution_frequency', 'member_limit', 'member_count', 'is_active', 'is_locked', 'manager')
    list_filter = ('is_active', 'is_locked', 'contribution_frequency')
    search_fields = ('name', 'manager__username')
    readonly_fields = ('member_count',)

@admin.register(PoolManagerAssignment)
class PoolManagerAssignmentAdmin(admin.ModelAdmin):
    list_display = ('pool', 'manager', 'assignment_date')
    search_fields = ('pool__name', 'manager__username')
