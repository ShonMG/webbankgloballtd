from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

def check_board_member_qualification(user):
    """
    Checks if a user qualifies to be a WebBank board member based on Amor108 membership criteria.
    Criteria: Must be an Amor108 member contributing Ksh 10,000 monthly.
    """
    try:
        # Check if the user is an Amor108 Member
        amor108_member = user.member  # Assumes a OneToOneField named 'member' on User, or similar reverse relation
                                    # Update: amor108.Member has user = OneToOneField, so user.member would work.

        # Check if the member has an assigned pool
        if not amor108_member.pool:
            return False, "User is an Amor108 member but not assigned to a pool."

        # Check the pool's contribution criteria
        if amor108_member.pool.contribution_amount == 10000 and \
           amor108_member.pool.contribution_frequency == 'monthly':
            return True, "User qualifies as a WebBank board member."
        else:
            return False, f"User's Amor108 pool ({amor108_member.pool.name}) does not meet the Ksh 10,000 monthly contribution requirement."

    except ObjectDoesNotExist:
        return False, "User is not an Amor108 member."
    except AttributeError:
        # This might happen if user.member doesn't exist or is not configured as expected
        return False, "Amor108 Member relation not found for this user."
    except Exception as e:
        return False, f"An unexpected error occurred during qualification check: {e}"