from django.contrib import admin
from .models import ProfitCycle, MemberProfit

@admin.register(ProfitCycle)
class ProfitCycleAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'total_profit_generated', 'total_distributed_profit', 'status', 'distributed_by')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('name', 'notes')
    date_hierarchy = 'start_date'
    raw_id_fields = ('distributed_by',)

@admin.register(MemberProfit)
class MemberProfitAdmin(admin.ModelAdmin):
    list_display = ('profit_cycle', 'member', 'allocated_profit', 'net_profit', 'action', 'action_date')
    list_filter = ('action', 'profit_cycle__name')
    search_fields = ('member__user__username', 'profit_cycle__name')
    raw_id_fields = ('profit_cycle', 'member', 'reinvestment_transaction')
