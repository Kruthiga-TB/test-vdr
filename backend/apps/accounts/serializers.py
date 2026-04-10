from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, InvitationToken, SubAdminPermission


class SuperAdminRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True)
    company_name = serializers.CharField(write_only=True)
    company_domain = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email',
            'name',
            'password',
            'confirm_password',
            'company_name',
            'company_domain',
            'region',
        ]

    PERSONAL_EMAIL_DOMAINS = [
    'yahoo.com', 'hotmail.com',
    'outlook.com', 'icloud.com', 'protonmail.com',
    'aol.com', 'mail.com', 'zoho.com'
]

    def validate_email(self, value):
        email_domain = value.split('@')[1]
        if email_domain in self.PERSONAL_EMAIL_DOMAINS:
            raise serializers.ValidationError(
                "Please use your company email address"
            )
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        return data


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class InvitationTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvitationToken
        fields = [
            'id',
            'email',
            'role',
            'status',
            'created_at',
            'expires_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'expires_at']


class InvitedUserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True)
    token = serializers.UUIDField(write_only=True)

    class Meta:
        model = User
        fields = [
            'name',
            'password',
            'confirm_password',
            'token',
        ]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        # Validate token exists and is valid
        try:
            token = InvitationToken.objects.get(token=data['token'])
            if not token.is_valid():
                raise serializers.ValidationError({
                    'token': 'Invitation link has expired or already been used'
                })
        except InvitationToken.DoesNotExist:
            raise serializers.ValidationError({
                'token': 'Invalid invitation token'
            })
        return data


class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'role',
            'is_active',
            'is_approved',
            'date_joined',
        ]
        read_only_fields = fields