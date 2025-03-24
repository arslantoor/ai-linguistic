"""Classes and functions required for JWT authentication."""

from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings


def allow_inactive_rule(user):
    """Allow inactive users to login."""
    if user is None:
        return False
    return True


class CustomJWTAuthentication(JWTAuthentication):
    """Allow inactive users to authenticate."""

    def get_user(self, validated_token):
        """Allow inactive users in requests."""
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_('Token contained no recognizable user identification'))

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_('User not found'), code='user_not_found')

        return user
