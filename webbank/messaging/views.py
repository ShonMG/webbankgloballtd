from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Conversation, Message, MessageTemplate, MessageGroup
from accounts.models import User
from .forms import MessageForm, ConversationForm, MessageGroupForm
from accounts.decorators import user_type_required
from django.contrib import messages as django_messages

@login_required
def inbox(request):
    """
    Displays a list of conversations for the current user.
    """
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    return render(request, 'messaging/inbox.html', {'conversations': conversations})

@login_required
def conversation_detail(request, conversation_id):
    """
    Displays the messages within a specific conversation.
    Allows sending new messages within the conversation.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    messages_in_conversation = conversation.messages.all().order_by('sent_at')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    # Mark messages as read by the current user
    for message in messages_in_conversation:
        if request.user not in message.read_by.all() and message.sender != request.user:
            message.read_by.add(request.user)

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'messages': messages_in_conversation,
        'form': form
    })

@login_required
def new_conversation(request):
    """
    Starts a new conversation with selected participants.
    """
    if request.method == 'POST':
        form = ConversationForm(request.POST, user=request.user) # Pass current user to form for participant choices
        if form.is_valid():
            recipient_users = form.cleaned_data['recipients']
            # Ensure the current user is a participant
            participants_list = list(recipient_users)
            if request.user not in participants_list:
                participants_list.append(request.user)

            # Check for existing conversation with exact same participants (order-independent)
            # This is a more complex check and might be simplified for a first pass,
            # or require a helper function. For now, we'll iterate.
            existing_conversation = None
            for conv in request.user.conversations.all():
                conv_participants = set(conv.participants.all())
                if conv_participants == set(participants_list):
                    existing_conversation = conv
                    break
            
            if existing_conversation:
                conversation = existing_conversation
            else:
                conversation = Conversation.objects.create()
                conversation.participants.set(participants_list)
                conversation.save()

            first_message_body = form.cleaned_data.get('body')
            first_message_subject = form.cleaned_data.get('subject') 
            if first_message_body:
                new_message_obj = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    subject=first_message_subject,
                    body=first_message_body
                )
                from notifications.utils import create_message_notification
                for recipient in recipient_users:
                    if recipient != request.user: # Don't notify sender about their own message
                        create_message_notification(new_message_obj, recipient)
            
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = ConversationForm(user=request.user)
    
    return render(request, 'messaging/new_conversation.html', {'form': form})

@login_required
def send_message(request, conversation_id):
    """
    Handles sending a message to an existing conversation (via POST only).
    This view is typically called by the form on conversation_detail page.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            from notifications.utils import create_message_notification
            for participant in conversation.participants.all():
                if participant != request.user: # Don't notify sender about their own message
                    create_message_notification(message, participant)
            
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    return redirect('messaging:conversation_detail', conversation_id=conversation.id)

@login_required
@user_type_required(['admin', 'founder']) # Only admins and founders can send broadcast messages
def send_broadcast_message(request):
    """
    Allows authorized users to send broadcast messages to predefined groups or all users.
    """
    if request.method == 'POST':
        form = MessageForm(request.POST)
        group_form = MessageGroupForm(request.POST) # For selecting existing groups or creating new ones implicitly

        if form.is_valid():
            body = form.cleaned_data['body']
            subject = form.cleaned_data.get('subject')
            
            # Determine recipients based on selected groups or 'all users'
            recipients = []
            
            # Example: If there's a field in the form to select groups or 'all'
            # For now, let's assume a simple case where an admin selects members from the groupform
            
            if group_form.is_valid() and group_form.cleaned_data.get('members'):
                recipients = group_form.cleaned_data['members']
            else: # Send to all users if no specific group is selected
                recipients = User.objects.all() 
            
            # Create a single broadcast message and link recipients
            broadcast_message_obj = Message.objects.create(
                sender=request.user,
                subject=subject,
                body=body,
                is_broadcast=True
            )
            broadcast_message_obj.recipients.set(recipients)

            from notifications.utils import create_message_notification
            for recipient in recipients:
                if recipient != request.user:
                    create_message_notification(broadcast_message_obj, recipient)
            
            django_messages.success(request, 'Broadcast message sent successfully!')
            return redirect('messaging:send_broadcast_message') # Redirect to the same page or a confirmation page
    else:
        form = MessageForm()
        group_form = MessageGroupForm()
    
    return render(request, 'messaging/send_broadcast_message.html', {
        'form': form,
        'group_form': group_form
    })

@login_required
@user_type_required(['admin', 'founder'])
def message_template_list(request):
    """
    Lists all available message templates.
    """
    templates = MessageTemplate.objects.all().order_by('name')
    return render(request, 'messaging/message_template_list.html', {'templates': templates})

@login_required
@user_type_required(['admin', 'founder'])
def message_template_create(request):
    """
    Allows creation of a new message template.
    """
    if request.method == 'POST':
        form = MessageTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Message template created successfully!')
            return redirect('messaging:message_template_list')
    else:
        form = MessageTemplateForm()
    return render(request, 'messaging/message_template_form.html', {'form': form, 'title': 'Create Message Template'})

@login_required
@user_type_required(['admin', 'founder'])
def message_template_update(request, pk):
    """
    Allows updating an existing message template.
    """
    template = get_object_or_404(MessageTemplate, pk=pk)
    if request.method == 'POST':
        form = MessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Message template updated successfully!')
            return redirect('messaging:message_template_list')
    else:
        form = MessageTemplateForm(instance=template)
    return render(request, 'messaging/message_template_form.html', {'form': form, 'title': 'Update Message Template'})

@login_required
@user_type_required(['admin', 'founder'])
def message_template_delete(request, pk):
    """
    Allows deletion of a message template.
    """
    template = get_object_or_404(MessageTemplate, pk=pk)
    if request.method == 'POST':
        template.delete()
        django_messages.success(request, 'Message template deleted successfully!')
        return redirect('messaging:message_template_list')
    return render(request, 'messaging/message_template_confirm_delete.html', {'template': template})