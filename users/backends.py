"""Backends required for users app."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class CustomModelBackend(ModelBackend):
    """Allow logging in from an inactive account."""

    def user_can_authenticate(self, user):
        """Allow user to login on inactive account."""
        return True
