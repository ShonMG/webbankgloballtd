from .models import Notification

def user_notifications(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at') # All notifications
        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
            'all_notifications': all_notifications, # Added all notifications
        }
    return {}