from django.db import models

# Create your models here.
import uuid
from django.db import models
from django.utils import timezone


class Company(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    
    # Used to validate superadmin registers with company email only
    # Example: techcorp.com — only @techcorp.com emails allowed
    domain = models.CharField(max_length=255, unique=True)
    
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    
    is_active = models.BooleanField(default=False)
    # Company becomes active only after owner approves superadmin

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Companies'


class Subscription(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='subscription'
    )

    storage_limit_gb = models.PositiveIntegerField(default=5)
    max_users = models.PositiveIntegerField(default=5)
    start_date = models.DateField()
    expiry_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        return timezone.now().date() <= self.expiry_date

    @property
    def is_expired(self):
        return timezone.now().date() > self.expiry_date

    @property
    def days_remaining(self):
        delta = self.expiry_date - timezone.now().date()
        return max(delta.days, 0)

    def __str__(self):
        return f"{self.company.name} - Subscription"