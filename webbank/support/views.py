from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time
import random
import string
from .models import SupportTicket
from .forms import SupportTicketForm

@login_required
def support_dashboard(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.ticket_id = f"TICK-{int(time.time())}{''.join(random.choices(string.digits, k=4))}"
            ticket.save()
            messages.success(request, 'Support ticket submitted successfully!')
            return redirect('support:support_dashboard')
    else:
        form = SupportTicketForm()
    
    user_tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'form': form,
        'user_tickets': user_tickets,
    }
    
    return render(request, 'support/support.html', context)