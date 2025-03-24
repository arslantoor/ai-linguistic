"""Utility functions for users."""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken

from users.token_generators import AccountActiveTokenGenerator

User = get_user_model()
logger = logging.getLogger(__name__)


def create_uid_and_token(user, token_generator=default_token_generator):
    """Create uid and token for user."""
    return urlsafe_base64_encode(force_bytes(user.pk)), token_generator.make_token(user)


def check_token(user, token, token_generator=default_token_generator):
    """Check if token is valid or not."""
    return token_generator.check_token(user, token)


def get_user_from_uidb64(uidb64):
    """Find user from uid64."""
    uid = urlsafe_base64_decode(uidb64).decode()
    return User.objects.get(pk=uid)


def activate_user(uidb64, token):
    """Activate a user from uid64 and token."""
    try:
        user = get_user_from_uidb64(uidb64)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        logger.warning(f'Cannot find user for uidb64:{uidb64}')
        return False, None

    if not check_token(user, token, token_generator=AccountActiveTokenGenerator()):
        return False, None
    user.is_active = True
    user.was_activated = True
    user.save(update_fields=['was_activated', 'is_active'])
    return True, user


def allow_sending_activation_email(user):
    """Check if we can send activation email for a user."""
    last_activation_email_sent_at = user.activation_email_sent_at
    if not last_activation_email_sent_at:
        return True
    if user.is_active or user.was_activated or settings.SKIP_ACTIVATION:
        return False
    return timezone.now() > last_activation_email_sent_at + timedelta(seconds=settings.ACTIVATION_EMAIL_RESEND_TIME)


def create_auth_data(user):
    from users.api.v1.serializers import UserSerializer
    user_serializer = UserSerializer(user)
    user_data = user_serializer.data
    tokens = RefreshToken.for_user(user)
    return {
        'access': str(tokens.access_token),
        'refresh': str(tokens),
        'user': user_data
    }
