from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User, InvitationToken
from .serializers import (
    SuperAdminRegistrationSerializer,
    UserLoginSerializer,
    InvitedUserRegistrationSerializer,
    InvitationTokenSerializer,
)
from .services import (
    send_otp_email,
    verify_otp,
    create_superadmin_and_company,
    send_invitation,
    register_invited_user,
    send_password_reset_email,
    reset_password,
    activate_superadmin,
)


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ─────────────────────────────────────────────
# SUPERADMIN REGISTRATION
# ─────────────────────────────────────────────

class RegistrationInitiateView(APIView):
    """
    Step 1 of registration
    Validates form data and sends OTP to email
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SuperAdminRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Check if email already registered
            if User.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Email already registered'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Send OTP to email
            send_otp_email(email)

            # Store registration data in session temporarily
            request.session['registration_data'] = serializer.validated_data
            request.session['registration_data']['password'] = \
                request.data.get('password')

            return Response(
                {'message': 'OTP sent to your email. Please verify.'},
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class RegistrationVerifyOTPView(APIView):
    """
    Step 2 of registration
    Verifies OTP and creates User + Company
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        print(f"Email: '{email}'")
        print(f"OTP entered: '{otp}'")
        print(f"Session data: {request.session.get('registration_data')}")

        if not email or not otp:
            return Response(
                {'error': 'Email and OTP are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify OTP
            verify_otp(email, otp)

            # Get registration data from session
            registration_data = request.session.get('registration_data')

            if not registration_data:
                return Response(
                    {'error': 'Registration session expired. Please start again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create user and company
            user, company = create_superadmin_and_company(registration_data)

            # Clear session
            del request.session['registration_data']

            return Response(
                {
                    'message': 'Registration successful. Waiting for owner approval.',
                    'email': user.email,
                    'company': company.name,
                },
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ─────────────────────────────────────────────
# ACCOUNT ACTIVATION
# ─────────────────────────────────────────────

class ActivateAccountView(APIView):
    """
    Called when SuperAdmin clicks activation link
    sent by owner after approval
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')

        if not email or not token:
            return Response(
                {'error': 'Email and token are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = activate_superadmin(email, token)
            return Response(
                {'message': 'Account activated successfully. You can now login.'},
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────

class LoginView(APIView):
    """
    Login for all user roles
    Returns JWT tokens on success
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(request, email=email, password=password)

            if not user:
                return Response(
                    {'error': 'Invalid email or password'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.is_approved:
                return Response(
                    {'error': 'Your account is pending owner approval'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if not user.is_active:
                return Response(
                    {'error': 'Please activate your account via the link sent to your email'},
                    status=status.HTTP_403_FORBIDDEN
                )

            tokens = get_tokens_for_user(user)

            return Response(
                {
                    'tokens': tokens,
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'name': user.name,
                        'role': user.role,
                    }
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ─────────────────────────────────────────────
# INVITATION
# ─────────────────────────────────────────────

class SendInvitationView(APIView):
    """
    SuperAdmin/Admin sends invitation to a new user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        role = request.data.get('role')

        if not email or not role:
            return Response(
                {'error': 'Email and role are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invitation = send_invitation(
                inviter=request.user,
                email=email,
                role=role
            )

            return Response(
                {
                    'message': f'Invitation sent to {email}',
                    'invitation_id': str(invitation.id),
                },
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class InvitedUserRegistrationView(APIView):
    """
    Called when invited user clicks link and registers
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitedUserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user = register_invited_user(serializer.validated_data)
                tokens = get_tokens_for_user(user)

                return Response(
                    {
                        'message': 'Registration successful.',
                        'tokens': tokens,
                        'user': {
                            'id': str(user.id),
                            'email': user.email,
                            'name': user.name,
                            'role': user.role,
                        }
                    },
                    status=status.HTTP_201_CREATED
                )

            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ─────────────────────────────────────────────
# PASSWORD RESET
# ─────────────────────────────────────────────

class PasswordResetRequestView(APIView):
    """
    User requests password reset link
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Always return success even if email not found
        # This prevents email enumeration attacks
        send_password_reset_email(email)

        return Response(
            {'message': 'If this email exists, a reset link has been sent.'},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    User submits new password with reset token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([email, token, new_password]):
            return Response(
                {'error': 'Email, token and new password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            reset_password(email, token, new_password)
            return Response(
                {'message': 'Password reset successful. You can now login.'},
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────

class LogoutView(APIView):
    """
    Blacklist refresh token on logout
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {'message': 'Logged out successfully'},
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )