from django.contrib.contenttypes.models import ContentType
from .models import Notification, NotificationSetting, NotificationTemplate
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def create_notification(user, title, message, notification_type='info', related_object=None):
    """
    Create a notification for a user
    """
    notification = Notification(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )
    
    if related_object:
        notification.related_object = related_object
    
    notification.save()
    return notification # Return the notification object

def send_email_notification(notification_instance, subject, email_message_body, recipient_list):
    """
    Sends an email notification.
    Checks global settings and user preferences before sending.
    """
    if not NotificationSetting.objects.filter(enable_email_notifications=True).exists():
        logger.info(f"Email notifications globally disabled. Not sending email for {notification_instance.id}.")
        return

    # In a more advanced system, you'd check individual user preferences too.
    # For now, we assume if global is on, and the user hasn't opted out (if such a setting existed).

    try:
        html_message = render_to_string('notifications/email_template.html', {
            'title': subject,
            'message': email_message_body,
            'notification': notification_instance,
            'user': notification_instance.user # Assuming notification_instance has a user
        })
        plain_message = strip_tags(html_message)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email notification sent for Notification ID: {notification_instance.id} to {recipient_list}")
    except Exception as e:
        logger.error(f"Failed to send email notification for Notification ID: {notification_instance.id}. Error: {e}")

def create_loan_approved_notification(loan):
    """Create notification when loan is approved"""
    notification = create_notification(
        user=loan.member,
        title="Loan Application Approved",
        message=f"Your {loan.loan_type.name} application for KES {loan.amount_approved} has been approved.",
        notification_type='loan_approved',
        related_object=loan
    )
    # Example of sending email if desired for this notification type
    # template = NotificationTemplate.objects.filter(notification_type='loan_approved').first()
    # if template and notification.user.email:
    #     subject = template.subject_template.format(loan_type=loan.loan_type.name)
    #     body = template.email_message_template.format(loan_type=loan.loan_type.name, amount=loan.amount_approved)
    #     send_email_notification(notification, subject, body, [notification.user.email])
    return notification

def create_loan_rejected_notification(loan):
    """Create notification when loan is rejected"""
    notification = create_notification(
        user=loan.member,
        title="Loan Application Rejected",
        message=f"Your {loan.loan_type.name} application for KES {loan.amount_applied} has been rejected.",
        notification_type='loan_rejected',
        related_object=loan
    )
    return notification

def create_share_purchase_notification(share_transaction):
    """Create notification for share purchase"""
    notification = create_notification(
        user=share_transaction.member,
        title="Share Purchase Successful",
        message=f"You have successfully purchased {share_transaction.units} shares for KES {share_transaction.total_amount}.",
        notification_type='share_purchase',
        related_object=share_transaction
    )
    return notification

def create_payment_due_notification(loan_repayment):
    """Create notification for due payment"""
    notification = create_notification(
        user=loan_repayment.loan.member,
        title="Payment Due Reminder",
        message=f"Your loan payment of KES {loan_repayment.amount} is due on {loan_repayment.due_date}.",
        notification_type='payment_due',
        related_object=loan_repayment
    )
    return notification

def create_guarantee_request_notification(guarantee, guarantor):
    """Create notification for guarantee request"""
    notification = create_notification(
        user=guarantor,
        title="Guarantee Request",
        message=f"You have been requested to guarantee a {guarantee.loan.loan_type.name} for {guarantee.loan.member.get_full_name()}.",
        notification_type='guarantee_request',
        related_object=guarantee
    )
    return notification

def create_loan_pending_manager_notification(loan):
    """Create notification when loan is pending manager approval"""
    # Notify the loan applicant
    notification = create_notification(
        user=loan.member,
        title="Loan Application Submitted",
        message=f"Your {loan.loan_type.name} application for KES {loan.amount_applied} has been submitted and is awaiting manager review.",
        notification_type='loan_pending_manager',
        related_object=loan
    )
    return notification
    # Potentially notify the manager (e.g., admin user who acts as manager)
    # For now, we only notify the applicant. Managers will see pending loans on their dashboard.

def create_loan_manager_approved_notification(loan):
    """Create notification when loan is approved by manager"""
    notification = create_notification(
        user=loan.member,
        title="Loan Application Reviewed by Manager",
        message=f"Your {loan.loan_type.name} application for KES {loan.amount_applied} has been approved by the manager and is now awaiting director review.",
        notification_type='loan_manager_approved',
        related_object=loan
    )
    return notification

def create_loan_manager_rejected_notification(loan):
    """Create notification when loan is rejected by manager"""
    notification = create_notification(
        user=loan.member,
        title="Loan Application Rejected by Manager",
        message=f"Your {loan.loan_type.name} application for KES {loan.amount_applied} has been rejected by the manager. Please review the comments for details.",
        notification_type='loan_manager_rejected',
        related_object=loan
    )
    return notification

def create_loan_director_approved_notification(loan):
    """Create notification when loan is approved by director (final approval)"""
    notification = create_notification(
        user=loan.member,
        title="Loan Application Approved by Director",
        message=f"Your {loan.loan_type.name} application for KES {loan.amount_applied} has been approved by the director and is now fully approved.",
        notification_type='loan_director_approved', # or loan_fully_approved
        related_object=loan
    )
    return notification
    # Consider adding another function for "loan_fully_approved" if there are further steps post-director approval

def create_loan_director_rejected_notification(loan):
    """Create notification when loan is rejected by director"""
    notification = create_notification(
        user=loan.member,
        title="Loan Application Rejected by Director",
        message=f"Your {loan.loan_type.name} application for KES {loan.amount_applied} has been rejected by the director. Please review the comments for details.",
        notification_type='loan_director_rejected',
        related_object=loan
    )
    return notification

def send_sms_notification(notification_instance, message_body, recipient_phone_number):
    """
    Sends an SMS notification.
    Checks global settings and user preferences before sending.
    This is a simulated function. In a real application, this would integrate with an SMS gateway.
    """
    if not NotificationSetting.objects.filter(enable_sms_notifications=True).exists():
        logger.info(f"SMS notifications globally disabled. Not sending SMS for {notification_instance.id}.")
        return

    # In a more advanced system, you'd check individual user preferences too.
    
    if not recipient_phone_number:
        logger.warning(f"No phone number provided for recipient of notification ID: {notification_instance.id}. SMS not sent.")
        return

    try:
        # Simulate sending SMS
        # In a real application:
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # client.messages.create(
        #     to=recipient_phone_number,
        #     from_=settings.TWILIO_PHONE_NUMBER,
        #     body=message_body
        # )
        logger.info(f"SIMULATED SMS sent for Notification ID: {notification_instance.id} to {recipient_phone_number}. Message: {message_body[:50]}...")
    except Exception as e:
        logger.error(f"Failed to send SIMULATED SMS notification for Notification ID: {notification_instance.id}. Error: {e}")

def create_message_notification(message_instance, recipient):
    """
    Creates an in-app notification for a new message and attempts to send an email and SMS.
    """
    title = f"New message from {message_instance.sender.get_full_name() or message_instance.sender.username}"
    message_body = message_instance.body[:100] + ('...' if len(message_instance.body) > 100 else '')
    
    notification = create_notification(
        user=recipient,
        title=title,
        message=message_body,
        notification_type='new_message',
        related_object=message_instance # Link to the message
    )

    # Attempt to send email if recipient has an email and templates are set up
    if recipient.email:
        template = NotificationTemplate.objects.filter(notification_type='new_message').first()
        if template:
            email_subject = template.subject_template.format(
                sender_name=message_instance.sender.get_full_name() or message_instance.sender.username,
                subject=message_instance.subject or 'No Subject'
            )
            email_body = template.email_message_template.format(
                sender_name=message_instance.sender.get_full_name() or message_instance.sender.username,
                message_body=message_instance.body,
                conversation_link=f"{settings.BASE_URL}/messaging/conversation/{message_instance.conversation.id}/" if message_instance.conversation else "#"
            )
            send_email_notification(notification, email_subject, email_body, [recipient.email])
        else:
            logger.warning(f"No email template found for 'new_message' type. Email not sent to {recipient.email}.")
    
    # Attempt to send SMS if recipient has a phone number and templates are set up
    if recipient.phone_number:
        template = NotificationTemplate.objects.filter(notification_type='new_message').first()
        if template:
            sms_message = template.sms_message_template.format(
                sender_name=message_instance.sender.get_full_name() or message_instance.sender.username,
                message_body=message_instance.body[:100] + '...' if len(message_instance.body) > 100 else message_instance.body,
            )
            send_sms_notification(notification, sms_message, recipient.phone_number)
        else:
            logger.warning(f"No SMS template found for 'new_message' type. SMS not sent to {recipient.phone_number}.")
    return notification