from django.urls import path
from trustees import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='trustee_dashboard'),
    path('students/', views.students_list_view, name='trustee_students'),
    path('students/<int:student_id>/', views.student_detail_view, name='trustee_student_detail'),
    path('feedback/', views.send_feedback_view, name='trustee_feedback'),
    path('mentors/', views.mentors_view, name='trustee_mentors'),
    path('analytics/', views.analytics_view, name='trustee_analytics'),
    path('analytics/api/', views.analytics_api, name='trustee_analytics_api'),
]
