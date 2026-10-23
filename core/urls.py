from django.urls import path
from core import views, admin_views

urlpatterns = [
    path('auth/login/', views.login_view, name='auth_login'),
    path('auth/logout/', views.logout_view, name='auth_logout'),
    path('auth/redirect/', views.role_redirect_view, name='role_redirect'),
    path('auth/change-password/', views.change_password_view, name='auth_change_password'),
    path('health/', views.health_check_view, name='health_check'),
    path('health/db/', views.db_health_check_view, name='health_check_db'),
    path('api/theme/toggle/', views.toggle_theme_view, name='toggle_theme'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read_view, name='mark_all_notifications_read'),
    
    # Custom Administration Routes
    path('admin/scholars/add/', admin_views.admin_student_add_view, name='admin_student_add'),
    path('admin-tools/scholars/add/', admin_views.admin_student_add_view),
    path('admin/mentors/add/', admin_views.admin_mentor_add_view, name='admin_mentor_add'),
    path('admin-tools/mentors/add/', admin_views.admin_mentor_add_view),
    path('admin/mentors/<int:mentor_id>/reset-password/', admin_views.admin_mentor_reset_password_view, name='admin_mentor_reset_password'),
    path('admin/import/audit/', admin_views.admin_import_view, name='admin_import_view'),
    path('admin-tools/import/audit/', admin_views.admin_import_view),
]

