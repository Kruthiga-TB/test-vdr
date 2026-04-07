# Create your models here.
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'owner')
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_approved', True)
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('sub_admin', 'Sub Admin'),
        ('external', 'External User'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='users'
    )
    
    invited_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invited_users'
    )

    is_active = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    region = models.CharField(max_length=100, null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # These two lines fix the clash
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='custom_user_set'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='custom_user_set'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return f"{self.name} ({self.role})"
    
# class SuperAdminProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     region = models.CharField(max_length=100)
#     company_name = models.CharField(max_length=255)

def invitation_expiry():
    return timezone.now() + timedelta(days=3)


class InvitationToken(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=invitation_expiry)

    def is_valid(self):
        return self.status == 'pending' and timezone.now() < self.expires_at

    def __str__(self):
        return f"Invitation for {self.email} ({self.role})"


class SubAdminPermission(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subadmin_permissions'
    )

    can_upload_documents = models.BooleanField(default=False)
    can_add_groups = models.BooleanField(default=False)
    can_invite_external_users = models.BooleanField(default=False)
    can_assign_permissions = models.BooleanField(default=False)
    can_view_activity_logs = models.BooleanField(default=False)
    can_respond_qna = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Permissions for {self.user.name}"


class NDAAcceptance(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='nda_acceptances'
    )
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='nda_acceptances'
    )

    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"NDA accepted by {self.user.name} at {self.accepted_at}"
    
def otp_expiry():
    return timezone.now() + timedelta(minutes=10)
    
class OTPVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    otp = models.CharField(max_length=64)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=otp_expiry)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.email}"