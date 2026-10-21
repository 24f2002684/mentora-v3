"""
URL configuration for Mentora project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Root redirects to role router
    path('', lambda request: redirect('role_redirect')),
    
    # Core authentication & administration
    path('', include('core.urls')),

    # Role specific modules
    path('student/', include('students.urls')),
    path('mentor/', include('mentors.urls')),
    path('trustee/', include('trustees.urls')),
    path('ai/', include('ai_assistant.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
