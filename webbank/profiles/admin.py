from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'approved')
    list_filter = ('approved',)
    search_fields = ('first_name', 'last_name', 'user__email')
    actions = ['approve_profiles']

    def approve_profiles(self, request, queryset):
        queryset.update(approved=True)
    approve_profiles.short_description = "Mark selected profiles as approved"