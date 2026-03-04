from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(role_name):
    """
    Decorator for views that checks if the user has a specific role
    in their Amor108Profile.
    """
    def check_role(user):
        if user.is_authenticated:
            try:
                amor108_profile = user.amor108profile
                if amor108_profile.role and amor108_profile.role.name == role_name:
                    return True
            except AttributeError:
                pass # User might not have an Amor108Profile yet
        raise PermissionDenied
    return user_passes_test(check_role)

def admin_required(function=None):
    return role_required('Admin')(function)

def pool_manager_required(function=None):
    return role_required('Pool Manager')(function)

def member_required(function=None):
    return role_required('Member')(function)

def non_member_borrower_required(function=None):
    return role_required('Non-member Borrower')(function)

def member_approval_required(function=None):
    """
    Decorator for views that checks if the user is authenticated and their
    Amor108 member status is 'Approved'.
    """
    def check_approval(user):
        if user.is_authenticated:
            if hasattr(user, 'amor108_member') and user.amor108_member.status and user.amor108_member.status.name == 'Approved':
                return True
        raise PermissionDenied
    return user_passes_test(check_approval)(function)