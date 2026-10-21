from django.urls import path
from ai_assistant import views

urlpatterns = [
    path('chat/', views.chat_view, name='ai_chat'),
    path('message/', views.send_message_api, name='ai_send_message'),
    path('conversations/<int:conv_id>/rename/', views.rename_conversation_api, name='ai_rename_conversation'),
    path('conversations/<int:conv_id>/delete/', views.delete_conversation_api, name='ai_delete_conversation'),
    path('activities/create/', views.create_activity_view, name='ai_create_activity'),
    path('activities/<int:activity_id>/submit/', views.submit_activity_view, name='ai_submit_activity'),
]
