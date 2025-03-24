"""Custom adapters for django-all-auth."""

from allauth.account.utils import perform_login
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social adapter for django-social-auth."""

    def pre_social_login(self, request, sociallogin):
        """Auto connect user account with same email on SSO."""
        user = sociallogin.user
        user.is_social_account = True
        if user.id:
            return

        try:
            new_user = User.objects.get(email=user.email)
            sociallogin.state['process'] = 'connect'
            perform_login(request, new_user, 'none')
        except User.DoesNotExist:
            pass

    def get_connect_redirect_url(self, request, socialaccount):
        """Go to homepage after connecting user."""
        return reverse(settings.LOGIN_REDIRECT_URL)
