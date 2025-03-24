"""Permissions required for users APIs."""

from django.conf import settings
from rest_framework.permissions import BasePermission, IsAuthenticated


class IsNotAuthenticated(BasePermission):
    """Permissions for URLs only accessible to non authenticated users."""

    def has_permission(self, request, view):
        """Check if user is not authenticated."""
        return request.user.is_anonymous


class IsAuthenticatedAndActivated(IsAuthenticated):
    """Permissions for URLs only accessible to authenticated and activated users."""

    def has_permission(self, request, view):
        """Check if user is authenticated and activated."""
        is_authenticated = super(IsAuthenticatedAndActivated, self).has_permission(request, view)
        return is_authenticated and request.user.is_active


class HasSignedAllAgreements(BasePermission):
    """Permission for URLs only accessible to users who have signed all agreements."""

    message = 'Please sign all assigned agreements.'

    def has_permission(self, request, view):
        """Check if a user has signed all assigned agreements."""
        return not settings.IS_TERMS_APP_ACTIVATED or request.user.profile.has_signed_all_terms
