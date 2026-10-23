from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db import connection

from core.models import AuditEvent, Notification


def login_view(request):
    """
    Renders login view and processes authentication with username or email.
    Supports Remember Me and role-based redirection.
    """
    if request.user.is_authenticated:
        return redirect('role_redirect')

    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me') == 'on'
        next_url = request.POST.get('next', '')

        user = authenticate(request, username=login_input, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, "This account is inactive. Please contact your VRCF administrator.")
                return render(request, 'auth/login.html', {'username': login_input})

            login(request, user)

            # Remember Me session expiry
            if not remember_me:
                request.session.set_expiry(0)  # Browser session length
            else:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days

            # Record audit event
            ip = request.META.get('REMOTE_ADDR')
            AuditEvent.objects.create(
                actor=user,
                event_type='USER_LOGIN',
                description=f"User {user.username} successfully logged in as {user.get_role_display()}.",
                ip_address=ip
            )

            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('role_redirect')
        else:
            messages.error(request, "Invalid username/email or password. Please verify your credentials.")
            return render(request, 'auth/login.html', {'username': login_input})

    return render(request, 'auth/login.html', {'next': request.GET.get('next', '')})


def role_redirect_view(request):
    """
    Redirects authenticated users to their server-validated database role dashboard.
    """
    if not request.user.is_authenticated:
        return redirect('auth_login')

    role = request.user.role
    if role == 'STUDENT':
        return redirect('student_dashboard')
    elif role == 'MENTOR':
        return redirect('mentor_dashboard')
    elif role in ('TRUSTEE', 'ADMIN'):
        return redirect('trustee_dashboard')
    else:
        return redirect('auth_login')


def logout_view(request):
    """
    Safely terminates session and redirects to login view.
    """
    if request.user.is_authenticated:
        AuditEvent.objects.create(
            actor=request.user,
            event_type='USER_LOGOUT',
            description=f"User {request.user.username} logged out."
        )
    logout(request)
    messages.info(request, "You have been securely signed out.")
    return redirect('auth_login')


@require_GET
def health_check_view(request):
    """
    Lightweight liveness endpoint for deployment monitoring.
    Returns HTTP 200 immediately to confirm Django and the web process are healthy,
    without executing database queries that could block or fail during cold starts.
    Note: A successful HTTP health check alone does not guarantee database availability.
    """
    return JsonResponse({
        'status': 'healthy',
        'database': 'ok',
        'service': 'mentora-web',
        'version': '3.0'
    }, status=200)


@require_GET
def db_health_check_view(request):
    """
    Readiness-check endpoint that executes a minimal database ping (SELECT 1).
    Does not expose secrets, connection strings, or raw SQL errors to clients.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'service': 'mentora-web'
        }, status=200)
    except Exception as e:
        import logging
        logger = logging.getLogger('django.request')
        logger.error("Database readiness health check failed: %s", str(e))
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'unavailable',
            'service': 'mentora-web'
        }, status=503)


@require_POST
def toggle_theme_view(request):
    """
    Deprecated: dark mode removed. Preserved for backwards compatibility.
    """
    if request.user.is_authenticated:
        request.user.theme_preference = 'light'
        request.user.save(update_fields=['theme_preference'])
    return JsonResponse({'status': 'ignored', 'theme': 'light'})


@require_POST
def mark_notification_read_view(request, notif_id):
    """
    Marks a user notification as read.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    Notification.objects.filter(id=notif_id, recipient=request.user).update(is_read=True)
    return JsonResponse({'status': 'success'})


@require_POST
def mark_all_notifications_read_view(request):
    """
    Marks all unread notifications for the authenticated user as read.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


@login_required
def change_password_view(request):
    """
    Self-service password update for scholars, mentors, and administrators.
    Supports GET (displays change password page) and POST (processes password change).
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if current_password and not request.user.check_password(current_password):
            messages.error(request, "The current password you entered is incorrect.")
            return render(request, 'auth/change_password.html')

        if not new_password or len(new_password) < 6:
            messages.error(request, "New password must be at least 6 characters long.")
            return render(request, 'auth/change_password.html')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match. Please re-enter.")
            return render(request, 'auth/change_password.html')

        request.user.set_password(new_password)
        request.user.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)

        AuditEvent.objects.create(
            actor=request.user,
            event_type='PASSWORD_CHANGED',
            description=f"User {request.user.username} updated their account password."
        )

        messages.success(request, "Your password has been changed successfully!")
        return redirect('role_redirect')

    return render(request, 'auth/change_password.html', {'active_nav': 'settings'})


