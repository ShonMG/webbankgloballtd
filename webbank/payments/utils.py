# webbank/payments/utils.py

import logging
from decimal import Decimal
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Wallet, WalletTransaction

logger = logging.getLogger(__name__)

def disburse_loan(loan):
    """
    Disburses a loan by crediting the member's wallet.
    For non-member loans, it also pays the guarantor's interest share immediately.
    This function is designed to be idempotent.
    """
    # Determine the borrower. Non-member loans are expected to have an amor108_member.
    # This logic assumes the borrower for a guest loan is still an amor108_member,
    # but the loan_type is what distinguishes it.
    borrower_member = loan.amor108_member
    if not borrower_member:
        logger.error(f"Loan {loan.loan_id} cannot be disbursed: no Amor108 member associated.")
        return

    wallet, created = Wallet.objects.get_or_create(member=borrower_member)
    if created:
        logger.info(f"Created wallet for member {borrower_member.user.username} during loan disbursement.")

    if loan.amount_approved is None or loan.amount_approved <= 0:
        logger.error(f"Loan {loan.loan_id} has no approved amount. Disbursement failed.")
        return

    # Idempotency check for disbursement
    loan_content_type = ContentType.objects.get_for_model(loan)
    if WalletTransaction.objects.filter(wallet=wallet, transaction_type='LOAN_DISBURSEMENT', object_id=loan.id, content_type=loan_content_type).exists():
        logger.warning(f"Loan {loan.loan_id} has already been disbursed to borrower. Skipping.")
        return

    # 1. Credit the borrower's wallet with the loan amount
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='LOAN_DISBURSEMENT',
        amount=loan.amount_approved,
        description=f"Loan disbursement for loan #{loan.loan_id}",
        content_object=loan
    )
    wallet.balance += loan.amount_approved
    wallet.save()
    logger.info(f"Successfully disbursed {loan.amount_approved} for loan {loan.loan_id} to wallet for {borrower_member.user.username}. New balance: {wallet.balance}")

    # 2. For non-member loans, credit the guarantor's wallet immediately
    if loan.loan_type.is_for_non_member and loan.guarantors.exists():
        guarantor = loan.guarantors.first() # Assuming one guarantor for simplicity
        guarantor_wallet, g_created = Wallet.objects.get_or_create(member=guarantor)
        if g_created:
            logger.info(f"Created wallet for guarantor {guarantor.user.username}.")

        guarantor_interest_amount = loan.amount_approved * loan.loan_type.guarantor_interest_share
        
        # Idempotency check for guarantor payment
        if not WalletTransaction.objects.filter(wallet=guarantor_wallet, transaction_type='FEE', description__contains=f"Interest share for guaranteeing loan #{loan.loan_id}").exists():
            WalletTransaction.objects.create(
                wallet=guarantor_wallet,
                transaction_type='FEE', # Or a more specific type like 'GUARANTOR_INTEREST'
                amount=guarantor_interest_amount,
                description=f"Interest share for guaranteeing loan #{loan.loan_id}",
                content_object=loan
            )
            guarantor_wallet.balance += guarantor_interest_amount
            guarantor_wallet.save()
            logger.info(f"Paid guarantor {guarantor.user.username} a share of {guarantor_interest_amount}. New wallet balance: {guarantor_wallet.balance}")
        else:
            logger.warning(f"Guarantor interest for loan {loan.loan_id} has already been paid. Skipping.")


    # 3. Finalize loan status
    loan.disbursement_date = timezone.now()
    loan.status = 'active'
    loan.save(update_fields=['disbursement_date', 'status'])
    
    logger.info(f"SIMULATING: M-Pesa B2C API call to send {loan.amount_approved} to member's phone.")
