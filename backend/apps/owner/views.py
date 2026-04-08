from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import User
from apps.accounts.services import approve_superadmin


# ─────────────────────────────────────────────
# OWNER PERMISSION
# ─────────────────────────────────────────────

class IsOwner(IsAuthenticated):
    """Only platform owner can access these views"""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and \
               request.user.role == 'owner'


# ─────────────────────────────────────────────
# PENDING REGISTRATIONS
# ─────────────────────────────────────────────

class PendingRegistrationsView(APIView):
    """
    List all SuperAdmins waiting for approval
    """
    permission_classes = [IsOwner]

    def get(self, request):
        pending_users = User.objects.filter(
            role='super_admin',
            is_approved=False,
            is_active=False
        ).select_related('company')

        data = [
            {
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'region': user.region,
                'company_name': user.company.name if user.company else None,
                'company_domain': user.company.domain if user.company else None,
                'registered_at': user.date_joined.strftime('%Y-%m-%d %H:%M'),
            }
            for user in pending_users
        ]

        return Response(
            {
                'count': len(data),
                'pending_registrations': data
            },
            status=status.HTTP_200_OK
        )


# ─────────────────────────────────────────────
# APPROVE SUPERADMIN
# ─────────────────────────────────────────────

class ApproveSuperAdminView(APIView):
    """
    Owner approves a pending SuperAdmin
    Triggers activation email
    """
    permission_classes = [IsOwner]

    def post(self, request, user_id):
        try:
            user = User.objects.get(
                id=user_id,
                role='super_admin',
                is_approved=False
            )

            approve_superadmin(user)

            return Response(
                {
                    'message': f'{user.name} has been approved. Activation link sent to {user.email}',
                },
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found or already approved'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ─────────────────────────────────────────────
# REJECT SUPERADMIN
# ─────────────────────────────────────────────

class RejectSuperAdminView(APIView):
    """
    Owner rejects a pending SuperAdmin
    Deletes user and company
    """
    permission_classes = [IsOwner]

    def post(self, request, user_id):
        try:
            user = User.objects.get(
                id=user_id,
                role='super_admin',
                is_approved=False
            )

            company = user.company
            user.delete()

            if company:
                company.delete()

            return Response(
                {'message': 'Registration rejected and removed.'},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found or already processed'},
                status=status.HTTP_404_NOT_FOUND
            )