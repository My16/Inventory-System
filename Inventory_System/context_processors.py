from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(recipient=request.user, is_read=False)[:5]
    else:
        notifications = []
    return {
        "notifications": notifications
    }
