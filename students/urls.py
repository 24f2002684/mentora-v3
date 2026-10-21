from django.urls import path
from students import views
from ai_assistant import views as ai_views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='student_dashboard'),
    path('profile/', views.profile_view, name='student_profile'),
    path('vision/', views.vision_view, name='student_vision'),
    path('goals/create/', views.goal_create_view, name='student_goal_create'),
    path('goals/<int:goal_id>/update/', views.goal_update_status_view, name='student_goal_update'),
    path('goals/<int:goal_id>/update-status/', views.goal_update_status_view, name='student_goal_update_status'),
    path('goals/<int:goal_id>/delete/', views.goal_delete_view, name='student_goal_delete'),
    path('learning-map/', views.learning_map_view, name='student_learning_map'),
    path('milestones/<int:milestone_id>/toggle/', views.milestone_toggle_view, name='student_milestone_toggle'),
    path('tasks/', views.tasks_view, name='student_tasks'),
    path('tasks/<int:task_id>/', views.task_detail_submit_view, name='student_task_submit'),
    path('self-tasks/create/', views.self_task_create_view, name='student_self_task_create'),
    path('self-tasks/<int:task_id>/toggle/', views.self_task_toggle_view, name='student_self_task_toggle'),
    path('tasks/self/<int:task_id>/toggle/', views.self_task_toggle_view),
    path('progress/', views.progress_view, name='student_progress'),
    path('progress/api/competencies/', views.competency_data_api, name='student_competency_api'),
    path('resources/', views.resources_view, name='student_resources'),
    path('resources/<int:resource_id>/save/', views.resource_save_toggle_view, name='student_resource_save'),
    path('settings/', views.settings_view, name='student_settings'),
    path('ai-mentor/', ai_views.chat_view, name='student_ai_mentor'),
    path('ai-mentor/chat/send/', ai_views.send_message_api, name='student_ai_send_message'),
    path('ai-mentor/conversations/<int:conv_id>/delete/', ai_views.delete_conversation_api, name='student_ai_delete_conv'),
    path('ai-mentor/conversations/<int:conv_id>/rename/', ai_views.rename_conversation_api, name='student_ai_rename_conv'),
    path('activities/create/', ai_views.create_activity_view, name='student_activity_create'),
    path('activities/<int:activity_id>/submit/', ai_views.submit_activity_view, name='student_activity_submit'),
]
