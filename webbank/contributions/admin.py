from django.contrib import admin
from .models import Contribution, ContributionStatus

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('member__user__username',)

@admin.register(ContributionStatus)
class ContributionStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
