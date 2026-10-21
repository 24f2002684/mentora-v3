from django.urls import path
from mentors import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='mentor_dashboard'),
    path('students/', views.students_list_view, name='mentor_students'),
    path('students/<int:student_id>/', views.student_detail_view, name='mentor_student_detail'),
    path('tasks/assign/', views.task_assign_view, name='mentor_task_assign'),
    path('submissions/', views.submissions_list_view, name='mentor_submissions'),
    path('submissions/<int:submission_id>/review/', views.submission_review_view, name='mentor_submission_review'),
    path('reports/', views.reports_view, name='mentor_reports'),
    path('reports/<int:student_id>/download/', views.download_pdf_report_view, name='mentor_report_download'),
    path('support-alerts/', views.support_alerts_view, name='mentor_support_alerts'),
]
