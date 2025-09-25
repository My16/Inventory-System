from .models import Notification
from .models import Office

def notifications_processor(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(recipient=request.user, is_read=False)[:5]
    else:
        notifications = []
    return {
        "notifications": notifications
    }

def offices_context(request):
    return {
        "offices": Office.objects.all()
    }