from rest_framework import serializers
from apps.accounts.models import User

class SuperAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'name', 'role', 'is_active', 'is_approved', 'date_joined', 'region', 'payment']
