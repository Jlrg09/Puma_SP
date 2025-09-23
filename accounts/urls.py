from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('waiting/', views.waiting, name='waiting'),
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('users/', views.users_list, name='users_list'),
    path('users/<int:user_id>/', views.user_edit, name='user_edit'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notif_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/read_all/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
        path('notifications/data/', views.notifications_data, name='notifications_data'),
    ]