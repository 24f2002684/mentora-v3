from core.models import Notification


def mentora_context(request):
    """
    Context processor providing global template variables:
    - user_profile (StudentProfile, MentorProfile, or TrusteeProfile)
    - unread_notifications_count
    - recent_notifications
    - user_role
    - app branding assets
    """
    context = {
        'APP_NAME': 'Mentora',
        'APP_VERSION': '3.0',
        'APP_TAGLINE': 'VRCF Student Development & Mentoring Platform',
        'user_profile': None,
        'user_role': None,
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }

    if request.user.is_authenticated:
        user = request.user
        context['user_role'] = user.role
        
        # Profile lookup based on role
        if hasattr(user, 'student_profile'):
            context['user_profile'] = user.student_profile
        elif hasattr(user, 'mentor_profile'):
            context['user_profile'] = user.mentor_profile
        elif hasattr(user, 'trustee_profile'):
            context['user_profile'] = user.trustee_profile

        # Notifications
        user_notifs = Notification.objects.filter(recipient=user)
        context['unread_notifications_count'] = user_notifs.filter(is_read=False).count()
        context['recent_notifications'] = user_notifs[:5]

    return context
