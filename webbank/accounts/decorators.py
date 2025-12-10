from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def user_type_required(allowed_roles):
    """
    Decorator for views that checks if the user has a specific user_type,
    redirecting to the login page if necessary.
    """
    if not isinstance(allowed_roles, (list, tuple)):
        allowed_roles = [allowed_roles]

    def check_user_type(user):
        if user.is_authenticated and user.user_type in allowed_roles:
            return True
        return False
    
    return user_passes_test(check_user_type, login_url='/accounts/signin/')


def member_required(function=None):
    actual_decorator = user_type_required('member')
    if function:
        return actual_decorator(function)
    return actual_decorator

def director_required(function=None):
    actual_decorator = user_type_required('director')
    if function:
        return actual_decorator(function)
    return actual_decorator

def admin_required(function=None):
    actual_decorator = user_type_required('admin')
    if function:
        return actual_decorator(function)
    return actual_decorator

def guarantor_required(function=None):
    actual_decorator = user_type_required('guarantor')
    if function:
        return actual_decorator(function)
    return actual_decorator

def founder_required(function=None):
    actual_decorator = user_type_required('founder')
    if function:
        return actual_decorator(function)
    return actual_decorator
