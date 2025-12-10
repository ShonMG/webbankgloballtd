from django.db import models
from django.db.models import Sum
from accounts.models import User
from decimal import Decimal

class LoanType(models.Model):
    name = models.CharField(max_length=100)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    max_term_months = models.IntegerField()
    description = models.TextField(blank=True)
    eligibility_criteria = models.TextField(blank=True, help_text="Criteria for loan eligibility")
    application_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
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
    
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    loan_id = models.CharField(max_length=20, unique=True)
    amount_applied = models.DecimalField(max_digits=12, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    disbursement_date = models.DateTimeField(null=True, blank=True)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # New fields for approval workflow
    approval_stage = models.CharField(max_length=20, choices=APPROVAL_STAGES, default='pending_manager')
    manager_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans_managed_approved')
    manager_approval_date = models.DateTimeField(null=True, blank=True)
    director_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans_director_approved')
    director_approval_date = models.DateTimeField(null=True, blank=True)
    approval_deadline = models.DateTimeField(null=True, blank=True)
    guarantors = models.ManyToManyField(
        User,
        related_name='guaranteed_loans',
        blank=True,
        limit_choices_to={'user_type': 'member'}, # Only members can be guarantors
        help_text="Select members who will guarantee this loan"
    )
    
    def calculate_monthly_payment(self):
        if self.amount_approved and self.interest_rate and self.term_months:
            monthly_rate = (self.interest_rate / 100) / 12
            payment = (self.amount_approved * monthly_rate * (1 + monthly_rate) ** self.term_months) / ((1 + monthly_rate) ** self.term_months - 1)
            return round(payment, 2)
        return 0
    
    def save(self, *args, **kwargs):
        if self.amount_approved and not self.monthly_payment:
            self.monthly_payment = self.calculate_monthly_payment()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.loan_id} - {self.member.username}"

    @property
    def total_paid(self):
        return self.repayments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or Decimal(0)

    @property
    def remaining_balance(self):
        if self.amount_approved:
            return self.amount_approved - self.total_paid
        return Decimal(0)

    @property
    def next_payment_date(self):
        next_repayment = self.repayments.filter(status__in=['due', 'overdue']).order_by('due_date').first()
        if next_repayment:
            return next_repayment.due_date
        return None

class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('due', 'Due'), ('overdue', 'Overdue')])
    transaction_id = models.CharField(max_length=50, unique=True)
    
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