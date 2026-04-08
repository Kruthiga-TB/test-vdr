import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import User, OTPVerification, InvitationToken



# ─────────────────────────────────────────────
# OTP SERVICES
# ─────────────────────────────────────────────

def generate_otp():
    """Generate a 6 digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(email):
    """
    Generate and send OTP to SuperAdmin email
    during registration for 2FA verification
    """
    email = email.strip().lower()

    otp = generate_otp()

    # First create new OTP
    new_otp = OTPVerification.objects.create(
        email=email,
        otp=otp,
    )

    # Invalidate any existing OTPs for this email
    OTPVerification.objects.filter(
        email=email,
        is_used=False
    ).exclude(id=new_otp.id).update(is_used=True)

    send_mail(
        subject='Verify your email - VDR Platform',
        message=f'''
        Your OTP for email verification is: {otp}
        
        This OTP is valid for 10 minutes.
        Do not share this with anyone.
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


def verify_otp(email, otp):
    """
    Verify OTP entered by SuperAdmin
    Returns True if valid, raises exception if not
    """
    email = email.strip().lower()
    otp = str(otp).strip()


    try:
        otp_obj = OTPVerification.objects.filter(
            email=email,
            otp=otp,
            is_used=False
        ).latest('created_at')

        if not otp_obj.is_valid():
            raise ValueError("OTP has expired. Please request a new one.")

        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save()
        return True

    except OTPVerification.DoesNotExist:
        raise ValueError("Invalid OTP. Please try again.")


# ─────────────────────────────────────────────
# SUPERADMIN REGISTRATION SERVICES
# ─────────────────────────────────────────────

def create_superadmin_and_company(validated_data):
    """
    After OTP verification:
    - Create Company (inactive)
    - Create SuperAdmin user (inactive, unapproved)
    - Notify owner for approval
    """
    from apps.companies.models import Company
   
    # Check if domain already registered
    if Company.objects.filter(domain=validated_data['company_domain']).exists():
        raise ValueError("A company with this domain already exists.")

    # Check if email already registered
    if User.objects.filter(email=validated_data['email']).exists():
        raise ValueError("This email is already registered.")

    company = Company.objects.create(
        name=validated_data['company_name'],
        domain=validated_data['company_domain'],
        is_active=False
    )

    # Create superadmin user
    user = User.objects.create_user(
        email=validated_data['email'],
        name=validated_data['name'],
        password=validated_data['password'],
        role='super_admin',
        company=company,
        region=validated_data.get('region'),
        is_active=False,
        is_approved=False,
    )

    # Notify owner about new registration
    notify_owner_new_registration(user, company)

    return user, company


def notify_owner_new_registration(user, company):
    """
    Send email to platform owner when
    a new SuperAdmin registers
    """
    send_mail(
        subject=f'New Registration Pending Approval - {company.name}',
        message=f'''
        A new company has registered on the VDR Platform.
        
        Details:
        Name        : {user.name}
        Email       : {user.email}
        Company     : {company.name}
        Domain      : {company.domain}
        Region      : {user.region}
        Registered  : {user.date_joined.strftime('%Y-%m-%d %H:%M')}
        
        Please login to the owner dashboard to review and approve.
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.OWNER_EMAIL],
        fail_silently=False,
    )


# ─────────────────────────────────────────────
# OWNER APPROVAL SERVICES
# ─────────────────────────────────────────────

def generate_activation_token():
    """Generate a secure random token for activation link"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=64))


def approve_superadmin(user):
    """
    Called when owner approves a SuperAdmin:
    - Mark user as approved
    - Generate activation token
    - Send activation link to SuperAdmin
    """
    # Mark as approved but still inactive until they click activation link
    user.is_approved = True
    user.save()

    # Generate activation token
    token = generate_activation_token()

    # Store token in OTPVerification reusing the model
    # We store token in otp field temporarily
    OTPVerification.objects.create(
        email=user.email,
        otp=token,
        expires_at=timezone.now() + timedelta(hours=24)
    )

    # Send activation link
    activation_link = f"{settings.FRONTEND_URL}/activate?token={token}&email={user.email}"

    send_mail(
        subject='Your VDR Account Has Been Approved',
        message=f'''
        Congratulations! Your registration has been approved.
        
        Click the link below to activate your account:
        {activation_link}
        
        This link is valid for 24 hours.
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )


def activate_superadmin(email, token):
    """
    Called when SuperAdmin clicks activation link:
    - Validate token
    - Activate user and company
    """
    email = email.strip().lower()
    token = str(token).strip()

    try:
        otp_obj = OTPVerification.objects.filter(
            email=email,
            otp=token,
            is_used=False
        ).latest('created_at')

        if not otp_obj.is_valid():
            raise ValueError("Activation link has expired.")

        user = User.objects.get(email=email)
        
        # Activate user
        user.is_active = True
        user.save()

        # Activate 
        user.company.is_active = True
        user.company.save()

        # Mark token as used
        otp_obj.is_used = True
        otp_obj.save()

        return user

    except OTPVerification.DoesNotExist:
        raise ValueError("Invalid activation link.")
    except User.DoesNotExist:
        raise ValueError("User not found.")


# ─────────────────────────────────────────────
# INVITATION SERVICES
# ─────────────────────────────────────────────

INVITATION_RULES = {
    'super_admin': ['admin', 'sub_admin', 'external'],
    'admin': ['sub_admin', 'external'],
    'sub_admin': ['external'],
}


def can_invite(inviter, role_to_invite):
    """
    Check if inviter is allowed to invite
    the given role
    """
    allowed_roles = INVITATION_RULES.get(inviter.role, [])
    return role_to_invite in allowed_roles


def send_invitation(inviter, email, role):
    """
    Send invitation email to a new user
    - Validates who can invite whom
    - Creates InvitationToken
    - Sends invitation email
    """
    # Check subadmin permission
    if inviter.role == 'sub_admin':
        if not hasattr(inviter, 'subadmin_permissions') or \
           not inviter.subadmin_permissions.can_invite_external_users:
            raise ValueError("You don't have permission to invite users.")

    # Check invitation rules
    if not can_invite(inviter, role):
        raise ValueError(f"You are not allowed to invite a {role}.")

    # Check if invitation already sent and pending
    existing = InvitationToken.objects.filter(
        email=email,
        company=inviter.company,
        status='pending'
    ).exists()

    if existing:
        raise ValueError("An invitation has already been sent to this email.")

    # Create invitation token
    invitation = InvitationToken.objects.create(
        email=email,
        role=role,
        company=inviter.company,
        invited_by=inviter,
    )

    # Send invitation email
    invite_link = f"{settings.FRONTEND_URL}/register?token={invitation.token}"

    send_mail(
        subject=f'You are invited to join {inviter.company.name} on VDR Platform',
        message=f'''
        You have been invited to join {inviter.company.name}.
        
        Click the link below to complete your registration:
        {invite_link}
        
        This invitation is valid for 3 days.
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )

    return invitation


# ─────────────────────────────────────────────
# INVITED USER REGISTRATION
# ─────────────────────────────────────────────

def register_invited_user(validated_data):
    """
    Called when invited user clicks link and registers:
    - Validate token
    - Create user with role from token
    - Mark token as accepted
    """
    token_obj = InvitationToken.objects.get(
        token=validated_data['token']
    )

    user = User.objects.create_user(
        email=token_obj.email,
        name=validated_data['name'],
        password=validated_data['password'],
        role=token_obj.role,
        company=token_obj.company,
        invited_by=token_obj.invited_by,
        is_active=True,
        is_approved=True,
    )

    # Mark invitation as accepted
    token_obj.status = 'accepted'
    token_obj.save()

    return user


# ─────────────────────────────────────────────
# PASSWORD RESET SERVICES
# ─────────────────────────────────────────────

def send_password_reset_email(email):
    """
    Send password reset link to user
    """
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        # Don't reveal if email exists or not
        return

    token = generate_activation_token()

    OTPVerification.objects.create(
        email=email,
        otp=token,
        expires_at=timezone.now() + timedelta(hours=1)
    )

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}&email={email}"

    send_mail(
        subject='Password Reset Request - VDR Platform',
        message=f'''
        You requested a password reset.
        
        Click the link below to reset your password:
        {reset_link}
        
        This link is valid for 1 hour.
        If you did not request this, please ignore this email.
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


def reset_password(email, token, new_password):
    """
    Validate token and reset password
    """
    email = email.strip().lower()
    token = str(token).strip()

    try:
        otp_obj = OTPVerification.objects.filter(
            email=email,
            otp=token,
            is_used=False
        ).latest('created_at')

        if not otp_obj.is_valid():
            raise ValueError("Reset link has expired.")

        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        otp_obj.is_used = True
        otp_obj.save()

        return user

    except OTPVerification.DoesNotExist:
        raise ValueError("Invalid or expired reset link.")