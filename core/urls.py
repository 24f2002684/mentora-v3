from django.urls import path
from core import views, admin_views

urlpatterns = [
    path('auth/login/', views.login_view, name='auth_login'),
    path('auth/logout/', views.logout_view, name='auth_logout'),
    path('auth/redirect/', views.role_redirect_view, name='role_redirect'),
    path('health/', views.health_check_view, name='health_check'),
    path('api/theme/toggle/', views.toggle_theme_view, name='toggle_theme'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('admin/scholars/add/', admin_views.admin_student_add_view, name='admin_student_add'),
    path('admin/import/audit/', admin_views.admin_import_view, name='admin_import_view'),
]
