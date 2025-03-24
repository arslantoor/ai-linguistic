"""Test cases for custom logic of django-all-auth."""

from allauth.account import app_settings as account_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import user_email, user_username
from allauth.socialaccount import providers
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialLogin
from allauth.socialaccount.tests import TestCase, override_settings
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from django.urls import reverse

from users.models import UserProfile

User = get_user_model()


class SocialAccountTests(TestCase):
    """Test cases for custom logic of django-all-auth."""

    def setUp(self):
        """Set up data for testing."""
        super(SocialAccountTests, self).setUp()
        for provider in providers.registry.get_list():
            SocialApp.objects.create(
                provider=provider.id,
                name=provider.id,
                client_id='app123id',
                key='123',
                secret='dummy',
            )

    def test_user_profile_created(self):
        """Test if user profile is created on social sign up."""
        factory = RequestFactory()
        request = factory.get('/accounts/login/callback/')
        request.user = AnonymousUser()
        SessionMiddleware(lambda request: None).process_request(request)
        MessageMiddleware(lambda request: None).process_request(request)

        user = User()
        setattr(user, account_settings.USER_MODEL_EMAIL_FIELD, 'test@example.com')

        account = SocialAccount(provider='google', uid='123')
        sociallogin = SocialLogin(user=user, account=account)
        complete_social_login(request, sociallogin)

        user = User.objects.get(**{account_settings.USER_MODEL_EMAIL_FIELD: 'test@example.com'})
        self.assertTrue(
            SocialAccount.objects.filter(user=user, uid=account.uid).exists()
        )
        self.assertTrue(
            EmailAddress.objects.filter(user=user, email=user_email(user)).exists()
        )
        self.assertTrue(
            UserProfile.objects.filter(user__email='test@example.com').exists()
        )

    def _email_address_clash(self, email):
        """Create data for email clash."""
        exi_user = User()
        user_username(exi_user, 'test')
        user_email(exi_user, 'test@example.com')
        exi_user.save()

        # A social user being signed up...
        account = SocialAccount(provider='google', uid='123')
        user = User()
        user_email(user, email)
        sociallogin = SocialLogin(user=user, account=account)

        # Signing up, should pop up the social signup form
        factory = RequestFactory()
        request = factory.get('/accounts/google/login/callback/')
        request.user = AnonymousUser()
        SessionMiddleware(lambda request: None).process_request(request)
        MessageMiddleware(lambda request: None).process_request(request)
        resp = complete_social_login(request, sociallogin)
        return request, resp

    def test_auto_connect_signup(self):
        """Test auto connect account on sign up."""
        request, response = self._email_address_clash('other@example.com')
        self.assertEqual(response['location'], reverse(settings.LOGIN_REDIRECT_URL))

    @override_settings(SKIP_ACTIVATION=False)
    def test_user_activated_account(self):
        """Test if user is active when using social account."""
        factory = RequestFactory()
        request = factory.get('/accounts/login/callback/')
        request.user = AnonymousUser()
        SessionMiddleware(lambda request: None).process_request(request)
        MessageMiddleware(lambda request: None).process_request(request)

        user = User()
        setattr(user, account_settings.USER_MODEL_EMAIL_FIELD, 'test@example.com')

        account = SocialAccount(provider='google', uid='123')
        sociallogin = SocialLogin(user=user, account=account)
        complete_social_login(request, sociallogin)

        user = User.objects.get(**{account_settings.USER_MODEL_EMAIL_FIELD: 'test@example.com'})
        self.assertTrue(user.is_active)
