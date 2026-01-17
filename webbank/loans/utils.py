from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from .models import Loan, LoanRepayment

def generate_repayment_schedule(loan: Loan):
    """
    Generates a repayment schedule for a given loan.
    Assumes fixed monthly payments with interest calculated on the outstanding principal.
    """
    if not loan.amount_approved or not loan.term_months:
        raise ValueError("Loan must have approved amount and term to generate schedule.")
    
    # Clear any existing repayments for this loan to ensure idempotency
    LoanRepayment.objects.filter(loan=loan).delete()

    outstanding_principal = loan.amount_approved
    
    # Handle simple interest for 1-month loans
    if loan.term_months == 1 and not loan.loan_type.is_for_non_member:
        interest_payment = (outstanding_principal * loan.loan_type.interest_rate).quantize(Decimal('0.01'))
        principal_payment = outstanding_principal
        current_due_date = (loan.disbursement_date.date() if loan.disbursement_date else date.today()) + relativedelta(months=1)
        
        LoanRepayment.objects.create(
            loan=loan,
            principal_amount=principal_payment,
            interest_amount=interest_payment,
            due_date=current_due_date,
            status='due',
        )

    # Handle amortized loans
    else:
        monthly_interest_rate = loan.loan_type.interest_rate / 12
        
        if monthly_interest_rate == 0:
            fixed_monthly_payment = (loan.amount_approved / loan.term_months).quantize(Decimal('0.01'))
        else:
            fixed_monthly_payment = (
                (loan.amount_approved * monthly_interest_rate) /
                (1 - (1 + monthly_interest_rate) ** -loan.term_months)
            ).quantize(Decimal('0.01'))

        current_due_date = loan.disbursement_date.date() if loan.disbursement_date else date.today()

        for i in range(loan.term_months):
            interest_payment = (outstanding_principal * monthly_interest_rate).quantize(Decimal('0.01'))
            principal_payment = fixed_monthly_payment - interest_payment

            # Adjust last payment to clear remaining principal due to rounding
            if i == loan.term_months - 1:
                principal_payment = outstanding_principal
            
            if principal_payment > outstanding_principal:
                 principal_payment = outstanding_principal

            outstanding_principal -= principal_payment
            
            current_due_date += relativedelta(months=1)

            LoanRepayment.objects.create(
                loan=loan,
                principal_amount=principal_payment,
                interest_amount=interest_payment,
                due_date=current_due_date,
                status='due',
            )

    # Update loan's next repayment date and monthly payment amount
    first_repayment = loan.repayments.order_by('due_date').first()
    if first_repayment:
        loan.next_repayment_date = first_repayment.due_date
        loan.monthly_payment = first_repayment.amount # Set the calculated payment amount
        loan.save(update_fields=['next_repayment_date', 'monthly_payment'])
