from .models import AuditLog
from django.db.models import Model # Import Model
from django.contrib.auth import get_user_model # To handle user=None for system actions

User = get_user_user_model() # Get the currently active user model

def log_admin_action(user, action, description, model_instance=None, ip_address=None):
    """
    Logs an administrative or significant system action.
    """
    model_name = None
    object_id = None
    if model_instance and isinstance(model_instance, Model):
        model_name = model_instance._meta.model_name
        object_id = str(model_instance.pk) # Convert PK to string for flexibility

    # Ensure user is a User instance, can be None for system actions
    user_instance = user if user and isinstance(user, User) else None
    
    AuditLog.objects.create(
        user=user_instance,
        action=action,
        description=description,
        model_name=model_name,
        object_id=object_id,
        ip_address=ip_address
    )
