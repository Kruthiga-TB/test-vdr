from rest_framework import serializers
from apps.accounts.models import User
from .models import Plan

class SuperAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'is_active', 'is_approved', 'date_joined', 'region', 'payment']

class SuperAdminApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email',
            'name',
            'is_approved',
            'region',
            'payment',

        ]


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id',
            'name',
            'price',
            'max_users',
            'storage_gb',
            'projects'
        ]
        read_only_fields = ['price', 'max_users', 'storage_gb', 'projects']