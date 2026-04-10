# from django.contrib.auth.backends import ModelBackend
# from django.contrib.auth import get_user_model

# User = get_user_model()

from apps.accounts.models import User

class EmailBackend:
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
            print(f"User found: {user.email}")
            print(f"Password check: {user.check_password(password)}")
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            print(f"No user found for email: {email}")
            return None