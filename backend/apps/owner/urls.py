from django.urls import path
from .views import (
    PendingRegistrationsView,
    ApproveSuperAdminView,
    RejectSuperAdminView,
)

urlpatterns = [
    path('pending/', PendingRegistrationsView.as_view(), name='pending-registrations'),
    path('approve/<uuid:user_id>/', ApproveSuperAdminView.as_view(), name='approve-superadmin'),
    path('reject/<uuid:user_id>/', RejectSuperAdminView.as_view(), name='reject-superadmin'),
]