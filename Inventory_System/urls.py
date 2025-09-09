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
    path("add-office/", views.add_office, name="add_office"),
    path('add-office/ajax/', views.add_office_ajax, name='add_office_ajax'),
    path("get-office/<int:office_id>/", views.get_office, name="get-office"),
    path("update-office/<int:office_id>/", views.update_office, name="update-office"),
    path("delete-office/<int:office_id>/", views.delete_office, name="delete-office"),
    path('list-users/', views.list_users, name='list_users'),
    path('create-user/', views.create_user, name='create_user'),
    path('change-password/<int:user_id>/', views.change_password, name='change_password'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('update-user-access/<int:user_id>/', views.update_user_access, name='update_user_access'),
    path("get-user-permissions/<int:user_id>/", views.get_user_permissions, name="get_user_permissions"),
    path("service-request/", views.service_request, name="service_request"),
    path('logout/', CustomLogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
    path('change-status/<int:request_id>/', views.change_status, name='change_status'),
    path("cancel-request/<int:request_id>/", views.cancel_service_request, name="cancel_service_request"),
    path("print_service_request/<int:pk>/", views.print_service_request, name="print_service_request"),
    path("encoding-error/", views.encoding_error, name="encoding_error"),
    path("encoding-error/change-status/", views.change_encoding_status, name="change_encoding_status"),
    path("encoding-error/edit/", views.edit_encoding_error, name="edit_encoding_error"),
    path("encoding-error/print/<int:pk>/", views.print_encoding_error, name="print_encoding_error"),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),

]