from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from .models import Loan, LoanRepayment

def generate_repayment_schedule(loan: Loan):
    """
    Generates a repayment schedule for a given loan.
    Assumes fixed monthly payments with interest calculated on the outstanding principal.
    """
    if not loan.amount_approved or not loan.term_months or not loan.loan_type.interest_rate:
        raise ValueError("Loan must have approved amount, term, and interest rate to generate schedule.")
    
    # Clear any existing repayments for this loan
    LoanRepayment.objects.filter(loan=loan).delete()

    outstanding_principal = loan.amount_approved
    monthly_interest_rate = loan.loan_type.interest_rate / 12

    # Calculate fixed monthly payment (PMT)
    # If interest rate is 0, simply divide principal by term
    if monthly_interest_rate == 0:
        fixed_monthly_payment = loan.amount_approved / loan.term_months
    else:
        # Standard annuity formula
        fixed_monthly_payment = (loan.amount_approved * monthly_interest_rate) /
                                (1 - (1 + monthly_interest_rate) ** -loan.term_months)
    fixed_monthly_payment = fixed_monthly_payment.quantize(Decimal('0.01'))

    current_due_date = loan.disbursement_date.date() if loan.disbursement_date else date.today()

    for i in range(loan.term_months):
        interest_payment = (outstanding_principal * monthly_interest_rate).quantize(Decimal('0.01'))
        
        # Ensure principal payment is not negative if it's the last payment
        principal_payment = fixed_monthly_payment - interest_payment
        if i == loan.term_months - 1: # For the last payment, adjust to clear remaining principal
            principal_payment = outstanding_principal
            fixed_monthly_payment = outstanding_principal + interest_payment

        # Ensure we don't overpay the principal due to rounding in last payment
        if principal_payment > outstanding_principal:
            principal_payment = outstanding_principal
            fixed_monthly_payment = outstanding_principal + interest_payment
        
        outstanding_principal -= principal_payment
        outstanding_principal = outstanding_principal.quantize(Decimal('0.01')) # Keep precision

        current_due_date = current_due_date + relativedelta(months=1)

        LoanRepayment.objects.create(
            loan=loan,
            amount=fixed_monthly_payment,
            due_date=current_due_date,
            status='due',
            # transaction_id will be added when payment is received
            # payment_transaction will be linked when payment is received
        )
    
    # Update loan's next repayment date
    first_repayment = LoanRepayment.objects.filter(loan=loan).order_by('due_date').first()
    if first_repayment:
        loan.next_repayment_date = first_repayment.due_date
        loan.save(update_fields=['next_repayment_date'])
