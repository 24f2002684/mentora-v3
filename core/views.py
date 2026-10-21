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
    Health-check endpoint for deployment monitoring and uptime verification.
    """
    db_status = 'ok'
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception as e:
        db_status = f'error: {str(e)}'

    status_code = 200 if db_status == 'ok' else 503
    return JsonResponse({
        'status': 'healthy' if db_status == 'ok' else 'unhealthy',
        'database': db_status,
        'app': 'Mentora VRCF',
        'version': '3.0'
    }, status=status_code)


@require_POST
def toggle_theme_view(request):
    """
    Updates user theme preference in database.
    """
    if request.user.is_authenticated:
        theme = request.POST.get('theme', 'light')
        if theme in ('light', 'dark', 'system'):
            request.user.theme_preference = theme
            request.user.save(update_fields=['theme_preference'])
            return JsonResponse({'status': 'success', 'theme': theme})
    return JsonResponse({'status': 'ignored'})


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
    """
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not new_password or len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect(request.META.get('HTTP_REFERER', 'role_redirect'))
            
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(request.META.get('HTTP_REFERER', 'role_redirect'))
            
        request.user.set_password(new_password)
        request.user.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        messages.success(request, "Your password has been successfully updated!")
        return redirect(request.META.get('HTTP_REFERER', 'role_redirect'))
        
    return redirect('role_redirect')

