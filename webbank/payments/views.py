from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decimal import Decimal
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PaymentTransaction, PaymentGatewayLog, Wallet, WalletTransaction
from contributions.models import Contribution, ContributionStatus
from members_amor108.models import Member as Amor108Member
from loans.models import Loan, LoanRepayment
from profits.utils import distribute_interest
import logging
import json

logger = logging.getLogger(__name__)

@csrf_exempt
def mpesa_callback_view(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            logger.info(f"M-Pesa Callback Received: {json.dumps(payload)}")

            gateway_log = PaymentGatewayLog.objects.create(
                payload=payload,
                gateway_name='M-Pesa'
            )

            trans_id = payload.get('TransID')
            if not trans_id:
                logger.error("M-Pesa callback missing transaction ID.")
                gateway_log.notes = "Callback missing transaction ID."
                gateway_log.save()
                return JsonResponse({"ResultCode": 1, "ResultDesc": "Missing Transaction ID"}, status=400)

            if PaymentTransaction.objects.filter(transaction_id=trans_id).exists():
                logger.warning(f"Duplicate M-Pesa transaction ID received: {trans_id}")
                gateway_log.notes = "Duplicate transaction ID received."
                gateway_log.is_processed = True
                gateway_log.save()
                return JsonResponse({"ResultCode": 0, "ResultDesc": "Duplicate Transaction ID"})

            trans_time_str = payload.get('TransTime')
            try:
                transaction_datetime = timezone.datetime.strptime(trans_time_str, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                transaction_datetime = timezone.now()

            payment_transaction = PaymentTransaction.objects.create(
                transaction_id=trans_id,
                amount=Decimal(payload.get('TransAmount', '0.00')),
                currency='KSH',
                status='COMPLETED',
                payment_method='MPESA_PAYBILL',
                sender_phone=payload.get('MSISDN'),
                sender_name=f"{payload.get('FirstName', '')} {payload.get('MiddleName', '')} {payload.get('LastName', '')}".strip(),
                shortcode=payload.get('BusinessShortCode'),
                invoice_number=payload.get('BillRefNumber'),
                transaction_time=transaction_datetime,
            )
            gateway_log.related_transaction = payment_transaction
            gateway_log.is_processed = True
            gateway_log.save()

            # Delegate processing to a separate function
            process_incoming_payment(payment_transaction)

            return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback received and processed successfully"})

        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error in M-Pesa callback: {e}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON Payload"}, status=400)
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {e}", exc_info=True)
            return JsonResponse({"ResultCode": 1, "ResultDesc": f"Internal Server Error: {e}"}, status=500)
    else:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request method"}, status=405)


def process_incoming_payment(payment_transaction):
    """
    Processes an incoming payment by depositing it into the member's wallet
    and then attempting to allocate the funds to outstanding receivables.
    """
    logger.info(f"Processing incoming payment {payment_transaction.transaction_id}")

    member = None
    if payment_transaction.invoice_number:
        try:
            # Assuming invoice number might be member's username OR a loan ID
            member = Amor108Member.objects.get(user__username=payment_transaction.invoice_number)
        except Amor108Member.DoesNotExist:
            try:
                loan = Loan.objects.get(loan_id=payment_transaction.invoice_number)
                member = loan.amor108_member
            except Loan.DoesNotExist:
                logger.warning(f"Could not find member or loan matching invoice_number: {payment_transaction.invoice_number}")
                payment_transaction.notes = f"Failed: No member or loan found for invoice '{payment_transaction.invoice_number}'."
                payment_transaction.status = 'FAILED'
                payment_transaction.save()
                return

    if not member:
        payment_transaction.notes = "Failed: No member could be identified for this transaction."
        payment_transaction.status = 'FAILED'
        payment_transaction.save()
        logger.warning(f"Payment {payment_transaction.transaction_id} could not be processed: No member identified.")
        return

    # Get or create the member's wallet
    wallet, created = Wallet.objects.get_or_create(member=member)
    if created:
        logger.info(f"Created wallet for member {member.user.username}")

    # Create a deposit transaction in the wallet
    wallet_tx = WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='DEPOSIT',
        amount=payment_transaction.amount,
        description=f"Deposit from {payment_transaction.payment_method} - Ref: {payment_transaction.transaction_id}",
        content_object=payment_transaction
    )
    
    # Update wallet balance
    wallet.balance += payment_transaction.amount
    wallet.save()

    logger.info(f"Successfully deposited {payment_transaction.amount} into wallet for {member.user.username}. New balance: {wallet.balance}")

    payment_transaction.notes += f" Processed and deposited to wallet {wallet.id}. Wallet tx id: {wallet_tx.id}."
    payment_transaction.save()

    allocate_funds_for_receivables(wallet)

def allocate_funds_for_receivables(wallet):
    """
    Uses a member's wallet balance to pay for outstanding receivables like contributions and loans.
    Priority: Contributions, then Loan Repayments.
    """
    logger.info(f"Allocating funds from wallet {wallet.id} for member {wallet.member.user.username}")

    # 1. Pay pending contributions
    try:
        paid_status = ContributionStatus.objects.get(name='Paid')
        pending_status = ContributionStatus.objects.filter(name__in=['Pending', 'Awaiting Payment'])
        if not pending_status.exists() or not paid_status:
            raise ContributionStatus.DoesNotExist
    except ContributionStatus.DoesNotExist:
        logger.error("Required ContributionStatus ('Paid', 'Pending'/'Awaiting Payment') not found.")
        return

    pending_contributions = Contribution.objects.filter(member=wallet.member, status__in=pending_status).order_by('date')
    for contrib in pending_contributions:
        if wallet.balance >= contrib.amount:
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='CONTRIBUTION',
                amount=-contrib.amount,
                description=f"Payment for contribution #{contrib.id}",
                content_object=contrib
            )
            wallet.balance -= contrib.amount
            wallet.save()
            contrib.status = paid_status
            contrib.save()
            logger.info(f"Paid contribution {contrib.id} for {wallet.member.user.username}. New balance: {wallet.balance}")
        else:
            break

    # 2. Pay due loan repayments
    due_repayments = LoanRepayment.objects.filter(
        loan__amor108_member=wallet.member, 
        status__in=['due', 'overdue']
    ).order_by('due_date')

    for repayment in due_repayments:
        if wallet.balance >= repayment.amount:
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='LOAN_REPAYMENT',
                amount=-repayment.amount,
                description=f"Repayment for loan {repayment.loan.loan_id}",
                content_object=repayment
            )
            wallet.balance -= repayment.amount
            wallet.save()

            repayment.status = 'paid'
            repayment.payment_date = timezone.now()
            repayment.save()
            
            # Update the parent loan's outstanding balance
            repayment.loan.save()

            # Distribute the interest component of the repayment
            distribute_interest(repayment)

            logger.info(f"Paid loan repayment {repayment.id} for {wallet.member.user.username}. New balance: {wallet.balance}")
        else:
            logger.info("Insufficient wallet balance for loan repayments.")
            break


class PaymentTransactionListView(LoginRequiredMixin, ListView):
    model = PaymentTransaction
    template_name = 'payments/payment_transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        # Filter transactions related to the logged-in user's contributions
        if hasattr(self.request.user, 'amor108_member'):
            member = self.request.user.amor108_member
            return PaymentTransaction.objects.filter(related_contribution__member=member).order_by('-transaction_time')
        return PaymentTransaction.objects.none()

class WalletDetailView(LoginRequiredMixin, DetailView):
    model = Wallet
    template_name = 'payments/wallet_detail.html'
    context_object_name = 'wallet'

    def get_object(self, queryset=None):
        """
        Get or create a wallet for the logged-in user.
        """
        if hasattr(self.request.user, 'amor108_member'):
            member = self.request.user.amor108_member
            wallet, created = Wallet.objects.get_or_create(member=member)
            if created:
                logger.info(f"Created wallet for member {member.user.username}")
            return wallet
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context['transactions'] = self.object.transactions.all()
        else:
            context['transactions'] = []
        return context

