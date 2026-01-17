from django.db import models
from django.db.models import Sum
from accounts.models import User
from members_amor108.models import Member as Amor108Member # Import Amor108Member
from payments.models import PaymentTransaction # Import PaymentTransaction
from decimal import Decimal

class LoanType(models.Model):
    name = models.CharField(max_length=100)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Total interest rate as a decimal (e.g., 0.20 for 20%)")
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    max_term_months = models.IntegerField()
    description = models.TextField(blank=True)
    eligibility_criteria = models.TextField(blank=True, help_text="Criteria for loan eligibility")
    application_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Fields for interest distribution
    is_for_non_member = models.BooleanField(default=False, help_text="Check if this loan type is for non-members (guests).")
    webbank_interest_share = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Portion of interest for WebBank (e.g., 0.02 for 2%).")
    guarantor_interest_share = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Portion of interest for the guarantor (e.g., 0.08 for 8%).")
    member_interest_share = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Portion of interest to be distributed among all members (e.g., 0.10 for 10%).")
    
    def __str__(self):
        return self.name

class Loan(models.Model):
    APPROVAL_STAGES = (
        ('pending_manager', 'Pending Manager Approval'),
        ('pending_director', 'Pending Director Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    LOAN_STATUS = (
        ('pending', 'Pending Review'),
        ('approved_manager', 'Approved by Manager'),
        ('approved_director', 'Approved by Director'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    )
    
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans_as_user', null=True, blank=True)
    amor108_member = models.ForeignKey(Amor108Member, on_delete=models.CASCADE, related_name='loans_as_amor108_member', null=True, blank=True)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    loan_id = models.CharField(max_length=20, unique=True)
    amount_applied = models.DecimalField(max_digits=12, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    term_months = models.IntegerField()
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    disbursement_date = models.DateTimeField(null=True, blank=True)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    outstanding_principal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Remaining principal balance")
    next_repayment_date = models.DateField(null=True, blank=True)
    last_repayment_date = models.DateField(null=True, blank=True)
    is_defaulted = models.BooleanField(default=False)

    # New fields for approval workflow
    approval_stage = models.CharField(max_length=20, choices=APPROVAL_STAGES, default='pending_manager')
    manager_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans_managed_approved')
    manager_approval_date = models.DateTimeField(null=True, blank=True)
    director_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans_director_approved')
    director_approval_date = models.DateTimeField(null=True, blank=True)
    approval_deadline = models.DateTimeField(null=True, blank=True)
    guarantors = models.ManyToManyField(
        'members_amor108.Member', # Link to members_amor108.Member
        related_name='guaranteed_loans',
        blank=True,
        help_text="Select members who will guarantee this loan"
    )
    sponsored_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sponsored_loans',
        help_text="The WebBank member who is sponsoring this guest loan."
    )
    
    def clean(self):
        super().clean()
        if not self.member and not self.amor108_member:
            raise ValidationError("A loan must be associated with either a WebBank User or an Amor108 Member.")
        if self.member and self.amor108_member:
            raise ValidationError("A loan cannot be associated with both a WebBank User and an Amor108 Member.")
    
    def calculate_monthly_payment(self):
        if self.amount_approved and self.loan_type.interest_rate and self.term_months:
            # For simple interest calculation (like one-month loans)
            if self.term_months == 1 and not self.loan_type.is_for_non_member:
                 total_interest = self.amount_approved * self.loan_type.interest_rate
                 return self.amount_approved + total_interest

            # For amortizing loans (long-term member loans and non-member loans)
            monthly_rate = self.loan_type.interest_rate / Decimal(12) if self.loan_type.interest_rate < 1 else self.loan_type.interest_rate
            if self.loan_type.is_for_non_member:
                monthly_rate = self.loan_type.interest_rate / Decimal(12) # Assuming 20% is annual

            if monthly_rate == 0:
                return round(self.amount_approved / self.term_months, 2)
            
            # Standard annuity formula for loan payment
            payment = (self.amount_approved * monthly_rate * (1 + monthly_rate) ** self.term_months) / ((1 + monthly_rate) ** self.term_months - 1)
            return round(payment, 2)
        return Decimal('0.00')
    
    def calculate_outstanding_balance(self):
        if self.amount_approved is None:
            return Decimal('0.00')
        
        total_repaid = self.repayments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return self.amount_approved - total_repaid # Simplified: does not account for interest accrual
        # More complex logic would involve amortizing principal and interest.

    def check_default_status(self):
        # A loan is defaulted if any scheduled repayment is overdue
        overdue_repayments = self.repayments.filter(status='overdue')
        self.is_defaulted = overdue_repayments.exists()
        self.save(update_fields=['is_defaulted'])

    def save(self, *args, **kwargs):
        from .utils import generate_repayment_schedule # Import here to avoid circular dependency

        if self.amount_approved and not self.monthly_payment:
            self.monthly_payment = self.calculate_monthly_payment()
        
        # When a loan is first approved and disbursed, set outstanding_principal
        # And generate repayment schedule
        if self.status == 'disbursed' and self.outstanding_principal is None:
            self.outstanding_principal = self.amount_approved
            # Generate repayment schedule only once when disbursed
            if not self.repayments.exists():
                if self.disbursement_date is None:
                    self.disbursement_date = timezone.now()
                generate_repayment_schedule(self)
                self.next_repayment_date = self.repayments.order_by('due_date').first().due_date
        
        # Update outstanding principal for active loans (if needed after repayments)
        elif self.status == 'active' and self.pk: # self.pk checks if object already exists
            self.outstanding_principal = self.calculate_outstanding_balance()
            self.check_default_status() # Check default status on save if active

        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.member:
            return f"{self.loan_id} - {self.member.username}"
        elif self.amor108_member:
            return f"{self.loan_id} - {self.amor108_member.user.username}"
        return f"{self.loan_id} - Guest"

    @property
    def total_paid(self):
        return self.repayments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    @property
    def remaining_balance(self):
        return self.outstanding_principal

    @property
    def next_payment_date(self):
        next_repayment = self.repayments.filter(status__in=['due', 'overdue']).order_by('due_date').first()
        if next_repayment:
            return next_repayment.due_date
        return None

class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('due', 'Due'), ('overdue', 'Overdue')])
    transaction_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    payment_transaction = models.OneToOneField(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='loan_repayment')
    
    @property
    def amount(self):
        return self.principal_amount + self.interest_amount

    def __str__(self):
        return f"Repayment for {self.loan.loan_id} - {self.amount}"

class LoanApprovalLog(models.Model):
    ACTION_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('commented', 'Commented'),
        ('forwarded', 'Forwarded for Director Approval'),
    )
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='approval_logs')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.loan.loan_id} - {self.action} by {self.approver.username if self.approver else 'N/A'}"