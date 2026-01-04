from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone

def get_next_expected_contribution_date(user_profile, reference_date=None):
    """
    Determines the next expected contribution date for a user based on their pool's
    frequency and their membership start date.
    """
    if not user_profile or not user_profile.membership_pool:
        return None

    pool = user_profile.membership_pool
    # Use the date the member joined the Sacco as the initial reference,
    # or the pool's creation date if member join date is not set.
    # More ideally, it would be the date the member joined *this specific pool*.
    # For now, let's use user.date_joined_sacco or default to pool creation date.
    if user_profile.user.date_joined_sacco:
        start_date = user_profile.user.date_joined_sacco
    else:
        start_date = pool.creation_date.date() # Ensure it's a date object

    today = timezone.now().date()
    if reference_date:
        today = reference_date

    if pool.contribution_frequency == 'MONTHLY':
        # Calculate next expected date based on the day of the month they joined
        expected_day = start_date.day

        # Start from the month of the reference date or start_date if it's in the future
        current_month = date(today.year, today.month, 1)

        # Iterate forward to find the next expected date
        next_expected_date = date(current_month.year, current_month.month, min(expected_day, 28))
        while next_expected_date < today:
            next_expected_date += relativedelta(months=1)
        
        # Adjust day if it exceeds month's last day (e.g., Feb 30th)
        try:
            next_expected_date = date(next_expected_date.year, next_expected_date.month, expected_day)
        except ValueError:
            # If expected_day is larger than the number of days in the month,
            # set it to the last day of the month.
            next_expected_date = date(next_expected_date.year, next_expected_date.month, 1) + relativedelta(months=1, days=-1)


        return next_expected_date

    elif pool.contribution_frequency == 'DAILY':
        # Simple daily: next day from reference_date
        return today + timedelta(days=1)
    
    return None

