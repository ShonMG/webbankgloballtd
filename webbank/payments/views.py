from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decimal import Decimal
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PaymentTransaction, PaymentGatewayLog
from contributions.models import Contribution, ContributionStatus
from members_amor108.models import Member as Amor108Member
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def mpesa_callback_view(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            logger.info(f"M-Pesa Callback Received: {json.dumps(payload)}")

            # Save raw payload to PaymentGatewayLog
            gateway_log = PaymentGatewayLog.objects.create(
                payload=payload,
                gateway_name='M-Pesa'
            )

            # Process the payload
            # This part is highly dependent on the actual M-Pesa API payload structure.
            # Below is a common structure for C2B (Customer to Business) transactions.
            # You might need to adjust based on your M-Pesa integration (e.g., STK Push, B2C, etc.)
            
            # For C2B Standard Payload (Validation/Confirmation URL)
            transaction_type = payload.get('TransactionType')
            trans_id = payload.get('TransID')
            trans_time = payload.get('TransTime')
            trans_amount = payload.get('TransAmount')
            business_short_code = payload.get('BusinessShortCode')
            bill_ref_number = payload.get('BillRefNumber') # This is usually the account number
            invoice_number = payload.get('InvoiceNumber') # Optional
            org_account_balance = payload.get('OrgAccountBalance') # Optional
            third_party_trans_id = payload.get('ThirdPartyTransID') # Optional
            msisdn = payload.get('MSISDN') # Sender's phone number
            first_name = payload.get('FirstName') # Optional
            middle_name = payload.get('MiddleName') # Optional
            last_name = payload.get('LastName') # Optional

            # Convert TransTime to a datetime object
            # M-Pesa TransTime format: YYYYMMDDHHmmss
            try:
                transaction_datetime = timezone.datetime.strptime(trans_time, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                transaction_datetime = timezone.now()
            
            # Check if transaction already exists to prevent duplicates
            if PaymentTransaction.objects.filter(transaction_id=trans_id).exists():
                logger.warning(f"Duplicate M-Pesa transaction ID received: {trans_id}")
                gateway_log.notes = "Duplicate transaction ID received."
                gateway_log.is_processed = True
                gateway_log.save()
                return JsonResponse({"ResultCode": 0, "ResultDesc": "Duplicate Transaction ID"})

            # Create PaymentTransaction
            payment_transaction = PaymentTransaction.objects.create(
                transaction_id=trans_id,
                amount=Decimal(trans_amount),
                currency='KSH', # Assuming KSH for M-Pesa
                status='COMPLETED', # Mark as completed upon successful callback
                payment_method='MPESA_PAYBILL',
                sender_phone=msisdn,
                sender_name=f"{first_name or ''} {middle_name or ''} {last_name or ''}".strip(),
                shortcode=business_short_code,
                invoice_number=bill_ref_number, # Use BillRefNumber as the invoice/reference
                transaction_time=transaction_datetime,
            )
            gateway_log.related_transaction = payment_transaction
            gateway_log.is_processed = True
            gateway_log.save()

            # Attempt to match to a Contribution
            match_payment_to_contribution(payment_transaction)

            return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback received and processed successfully"})

        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error in M-Pesa callback: {e}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON Payload"}, status=400)
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {e}", exc_info=True)
            return JsonResponse({"ResultCode": 1, "ResultDesc": f"Internal Server Error: {e}"}, status=500)
    else:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request method"}, status=405)


def match_payment_to_contribution(payment_transaction):
    """
    Attempts to match a PaymentTransaction to an existing Contribution.
    Logic can be expanded based on business rules (e.g., matching by amount, date, member ID).
    """
    logger.info(f"Attempting to match payment {payment_transaction.transaction_id} to a contribution.")

    # Get the 'Paid' status for contributions
    try:
        paid_status = ContributionStatus.objects.get(name='Paid')
    except ContributionStatus.DoesNotExist:
        logger.error("ContributionStatus 'Paid' does not exist. Please create it in admin.")
        return False

    # A common matching strategy: using invoice_number as member's ID or contribution reference
    # Assuming invoice_number (BillRefNumber) contains a unique identifier for the member
    # or a specific contribution reference.
    if payment_transaction.invoice_number:
        # Try to find an Amor108Member by their username (which could be the invoice_number)
        try:
            member = Amor108Member.objects.get(user__username=payment_transaction.invoice_number)
            
            # Check for existing pending contributions for this member and amount
            # Or create a new contribution if none exists and the payment matches expected behavior
            
            # For simplicity, let's assume we create a new contribution upon receiving payment
            # This logic needs to be refined based on how contributions are pre-created or expected.
            
            # If the payment is meant for a specific expected contribution, you'd query for it here
            # For example: contribution = Contribution.objects.get(member=member, status='PENDING', expected_amount=payment_transaction.amount)

            # If not found, let's assume this payment directly results in a new 'Paid' contribution
            contribution, created = Contribution.objects.get_or_create(
                member=member,
                amount=payment_transaction.amount,
                date=payment_transaction.transaction_time.date(),
                defaults={'status': paid_status}
            )
            
            # If created, link payment and update status
            if created:
                payment_transaction.related_contribution = contribution
                payment_transaction.status = 'COMPLETED'
                payment_transaction.save()
                logger.info(f"Payment {payment_transaction.transaction_id} successfully created and matched to new contribution {contribution.id}.")
                return True
            else:
                # If a contribution with same member, amount, date exists, update its status
                # and link if it was pending or initiated.
                if contribution.status.name != 'Paid':
                    contribution.status = paid_status
                    contribution.save()
                    payment_transaction.related_contribution = contribution
                    payment_transaction.status = 'COMPLETED'
                    payment_transaction.save()
                    logger.info(f"Payment {payment_transaction.transaction_id} matched to existing contribution {contribution.id} and updated status.")
                    return True
                else:
                    logger.info(f"Payment {payment_transaction.transaction_id} found matching paid contribution {contribution.id}. Possible duplicate or already processed.")
                    payment_transaction.notes += "\nMatched to an already paid contribution."
                    payment_transaction.save()
                    return False


        except Amor108Member.DoesNotExist:
            logger.warning(f"No Amor108Member found with username matching invoice_number: {payment_transaction.invoice_number}")
            payment_transaction.notes += f"\nNo member found with username '{payment_transaction.invoice_number}'."
            payment_transaction.status = 'FAILED' # Or 'PENDING_REVIEW'
            payment_transaction.save()
            return False
        except Exception as e:
            logger.error(f"Error matching payment {payment_transaction.transaction_id} to contribution: {e}", exc_info=True)
            payment_transaction.notes += f"\nError during matching: {e}"
            payment_transaction.status = 'FAILED' # Or 'PENDING_REVIEW'
            payment_transaction.save()
            return False
    
    payment_transaction.notes += "\nNo invoice number provided for matching."
    payment_transaction.status = 'FAILED' # Or 'PENDING_REVIEW'
    payment_transaction.save()
    logger.warning(f"Payment {payment_transaction.transaction_id} could not be matched: No invoice number.")
    return False


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

