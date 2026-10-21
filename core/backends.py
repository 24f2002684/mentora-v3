from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Allows authentication using either normalized email or username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        if not username or not password:
            return None

        # Clean username/email input
        login_identifier = str(username).strip()
        
        try:
            # Query by exact username or case-insensitive email
            user = UserModel.objects.filter(
                Q(username__iexact=login_identifier) | Q(email__iexact=login_identifier)
            ).first()
            
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        except Exception:
            return None
        return None
