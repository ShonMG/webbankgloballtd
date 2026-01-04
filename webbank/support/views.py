from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time
import random
import string
from .models import SupportTicket
from .forms import SupportTicketForm

@login_required
def support_dashboard(request):
    """
    Renders the support dashboard page.
    """
    return render(request, 'support/dashboard.html')


@login_required
def ticket_list(request):
    user_tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'user_tickets': user_tickets,
    }
    
    return render(request, 'support/ticket_list.html', context)

@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.ticket_id = f"TICK-{int(time.time())}{''.join(random.choices(string.digits, k=4))}"
            ticket.save()
            messages.success(request, 'Support ticket submitted successfully!')
            return redirect('support:ticket_list') # Redirect to ticket list after creation
    else:
        form = SupportTicketForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'support/create_ticket.html', context) # Render a dedicated template for create_ticket

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    
    context = {
        'ticket': ticket,
    }
    
    return render(request, 'support/ticket_detail.html', context)