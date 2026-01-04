from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q # Import Q for complex lookups
from .models import Guarantee
from loans.models import Loan # Import Loan model to check for loans associated with the user

@login_required
def guarantees_dashboard(request):
    user = request.user
    
    search_query = request.GET.get('q', '') # Get the search query from GET parameters

    given_guarantees = Guarantee.objects.filter(guarantor=user)
    
    # Apply search filter if query exists
    if search_query:
        given_guarantees = given_guarantees.filter(
            Q(loan__loan_id__icontains=search_query) |
            Q(loan__loan_type__name__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Guarantees for loans taken by the current user that are pending
    # This assumes a loan can have multiple guarantees
    pending_guarantees_on_my_loans = Guarantee.objects.filter(
        loan__member=user,
        status='pending'
    ).exclude(guarantor=user) # Exclude guarantees given by self if they are also the borrower

    # Apply search filter to pending guarantees on my loans
    if search_query:
        pending_guarantees_on_my_loans = pending_guarantees_on_my_loans.filter(
            Q(loan__loan_id__icontains=search_query) |
            Q(loan__loan_type__name__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Guarantees the current user has given, which are still pending
    # This relies on the filtered given_guarantees
    pending_guarantees_given_by_me = given_guarantees.filter(status='pending')

    # Combine all pending guarantees relevant to the user for display
    all_pending_guarantees = (pending_guarantees_on_my_loans | pending_guarantees_given_by_me).distinct()


    # Statistics
    total_guarantees = given_guarantees.count()
    active_guarantees = given_guarantees.filter(status='active').count()
    total_amount = given_guarantees.aggregate(total=Sum('amount_guaranteed'))['total'] or 0
    at_risk = given_guarantees.filter(loan__status='defaulted').count()
    
    context = {
        'guarantees': given_guarantees, # Guarantees given by the user
        'all_pending_guarantees': all_pending_guarantees, # All pending guarantees relevant to the user
        'total_guarantees': total_guarantees,
        'active_guarantees': active_guarantees,
        'total_amount': total_amount,
        'at_risk': at_risk,
        'search_query': search_query, # Pass search query to template
    }
    
    return render(request, 'guarantees/guarantees.html', context)