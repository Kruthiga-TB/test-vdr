from django.urls import path
from .views import (
    RegistrationInitiateView,
    RegistrationVerifyOTPView,
    ActivateAccountView,
    LoginView,
    SendInvitationView,
    InvitedUserRegistrationView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    LogoutView,
)

urlpatterns = [
    # Registration
    path('register/', RegistrationInitiateView.as_view(), name='register'),
    path('register/verify-otp/', RegistrationVerifyOTPView.as_view(), name='verify-otp'),

    # Activation
    path('activate/', ActivateAccountView.as_view(), name='activate'),

    # Login / Logout
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Invitation
    path('invite/', SendInvitationView.as_view(), name='invite'),
    path('invite/register/', InvitedUserRegistrationView.as_view(), name='invite-register'),

    # Password Reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]