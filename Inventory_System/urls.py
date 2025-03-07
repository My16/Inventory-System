from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.contrib import messages

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have successfully logged out.")
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
    path('', views.loginPage, name='loginpage'),
    path('login/', views.user_login, name='login'),
    path('homepage/', views.homepage, name='homepage'),
    path('logout/', CustomLogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
]