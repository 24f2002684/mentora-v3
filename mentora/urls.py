"""
URL configuration for Mentora project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.shortcuts import redirect

urlpatterns = [
    # Core authentication & administration (must be before admin.site.urls to avoid catch-all interception)
    path('', include('core.urls')),

    path('admin/', admin.site.urls),
    
    # Root redirects to role router
    path('', lambda request: redirect('role_redirect')),

    # Role specific modules
    path('student/', include('students.urls')),
    path('mentor/', include('mentors.urls')),
    path('trustee/', include('trustees.urls')),
    path('ai/', include('ai_assistant.urls')),

    # User uploaded media assets (profile photos, vision boards, submission attachments)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
