from django.contrib import admin
from .models import LoanType, Loan, LoanRepayment, LoanApprovalLog

@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'interest_rate', 'is_for_non_member', 'webbank_interest_share', 'guarantor_interest_share', 'member_interest_share', 'max_term_months')
    list_filter = ('is_for_non_member',)
    search_fields = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'interest_rate', 'max_amount', 'min_amount', 'max_term_months', 'description', 'eligibility_criteria')
        }),
        ('Interest Distribution (For Non-Member Loans)', {
            'classes': ('collapse',),
            'fields': ('is_for_non_member', 'webbank_interest_share', 'guarantor_interest_share', 'member_interest_share'),
        }),
        ('Fees', {
            'classes': ('collapse',),
            'fields': ('application_fee', 'processing_fee'),
        }),
    )

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_id', 'get_borrower', 'loan_type', 'amount_approved', 'status', 'application_date', 'is_defaulted', 'next_repayment_date')
    list_filter = ('status', 'loan_type', 'is_defaulted', 'approval_stage')
    search_fields = ('loan_id', 'member__username', 'amor108_member__user__username')
    raw_id_fields = ('member', 'amor108_member', 'guarantors', 'manager_approved_by', 'director_approved_by')
    readonly_fields = ('monthly_payment', 'outstanding_principal', 'next_repayment_date', 'last_repayment_date', 'is_defaulted')
    
    def get_borrower(self, obj):
        if obj.member:
            return f"WebBank: {obj.member.username}"
        elif obj.amor108_member:
            return f"Amor108: {obj.amor108_member.user.username}"
        return "N/A"
    get_borrower.short_description = 'Borrower'

    def save_model(self, request, obj, form, change):
        # Call the full_clean method to run model's clean() method and field validation
        obj.full_clean()
        super().save_model(request, obj, form, change)

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'due_date', 'status', 'payment_date')
    list_filter = ('status', 'due_date')
    search_fields = ('loan__loan_id', 'loan__member__username', 'loan__amor108_member__user__username', 'transaction_id')
    raw_id_fields = ('loan', 'payment_transaction')

@admin.register(LoanApprovalLog)
class LoanApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('loan', 'approver', 'action', 'timestamp')
    list_filter = ('action',)
    search_fields = ('loan__loan_id', 'approver__username', 'comments')
