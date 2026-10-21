from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Decorator that checks if the user is authenticated and belongs to one of allowed_roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/auth/login/?next={request.path}")
            
            # Superusers or Admins can access all management panels
            if request.user.is_superuser or request.user.role == 'ADMIN':
                return view_func(request, *args, **kwargs)

            if request.user.role not in allowed_roles:
                messages.error(request, "Access denied. You do not have permission to view that resource.")
                # Redirect to their appropriate dashboard
                if request.user.role == 'STUDENT':
                    return redirect('student_dashboard')
                elif request.user.role == 'MENTOR':
                    return redirect('mentor_dashboard')
                elif request.user.role == 'TRUSTEE':
                    return redirect('trustee_dashboard')
                return redirect('auth_login')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def student_required(view_func):
    return role_required('STUDENT')(view_func)


def mentor_required(view_func):
    return role_required('MENTOR')(view_func)


def trustee_required(view_func):
    return role_required('TRUSTEE')(view_func)


def admin_required(view_func):
    return role_required('ADMIN')(view_func)
