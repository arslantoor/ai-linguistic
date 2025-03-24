"""Tests for users app."""

from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from users.models import UserProfile
from users.token_generators import AccountActiveTokenGenerator
from users.utils import create_uid_and_token
from core.tasks import send_email

User = get_user_model()


class CustomUserTest(TestCase):
    """Test cases for custom user model."""

    def setUp(self):
        """Set up data for testing."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )

    def test_create_user(self):
        """Test user creation."""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpassword'))
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_create_user_profile(self):
        """Test creation of UserProfile model."""
        self.assertTrue(UserProfile.objects.get(user=self.user))

    def test_create_staff_user(self):
        """Test superuser creation."""
        admin_user = User.objects.create_staff(
            email='staff@example.com',
            password='adminpassword'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertFalse(admin_user.is_superuser)

    def test_create_superuser(self):
        """Test superuser creation."""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpassword'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class SignupViewTest(TestCase):
    """Test cases for SignupView."""

    def setUp(self):
        """Set up test data for testing."""
        self.url = reverse('signup')
        self.user_data = {
            'email': 'test@example.com',
            'password1': 'testpassword',
            'password2': 'testpassword'
        }

    def test_signup_page_loads_successfully(self):
        """Test if sign up page loads successfully."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')

    def test_signup_form_valid(self):
        """Test if user is created through signup page."""
        response = self.client.post(self.url, data=self.user_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
        self.assertTrue(UserProfile.objects.filter(user__email=self.user_data['email']).exists())

    def test_signup_form_submission_failure(self):
        """Test sign up failure on empty parameters."""
        response = self.client.post(self.url, data={}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')
        self.assertContains(response, 'This field is required.')

    def test_signup_form_no_email(self):
        """Test input on no email entered."""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = ''
        response = self.client.post(self.url, data=self.user_data)
        self.assertEqual(response.status_code, 302)

    def test_signup_form_different_passwords(self):
        """Test form on mismatching passwords."""
        invalid_data = self.user_data.copy()
        invalid_data['password2'] = 'differentpassword'
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')
        self.assertContains(response, 'The two password fields didn’t match.')


class LoginViewTest(TestCase):
    """Test cases for LoginView."""

    def setUp(self):
        """Set up data for testing."""
        self.url = reverse('login')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        self.valid_data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        self.invalid_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }

    def test_login_view(self):
        """Test login view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_form_valid(self):
        """Test login form on valid inputs."""
        response = self.client.post(self.url, data=self.valid_data)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email=self.valid_data['email'])
        self.assertTrue(user.is_authenticated)

    def test_login_form_invalid(self):
        """Test login form on invalid inputs."""
        response = self.client.post(self.url, data=self.invalid_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')


class LogoutViewTest(TestCase):
    """Test cases for LogoutView."""

    def setUp(self):
        """Set up data for testing."""
        self.url = reverse('logout')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        self.client.login(email='test@example.com', password='testpassword')

    def test_logout_view(self):
        """Test logout view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertFalse(self.client.session.get('_auth_user_id', False))


class PasswordResetTests(TestCase):
    """Test the password reset feature."""

    def setUp(self):
        """Set up data for testing."""
        self.url = reverse_lazy('password_reset')
        self.success_url = reverse_lazy('password_reset_done')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpassword',
        }
        self.user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

    def test_password_reset_form_loads_successfully(self):
        """Test password reset view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_password_reset_email_sent_successfully(self):
        """Test if password reset email is being sent."""
        if not settings.IS_EMAIL_SENDING_ENABLED:
            return
        with patch('core.tasks.send_email.apply_async') as mock_apply_async:
            response = self.client.post(self.url, {'email': self.user_data['email']})
            task_args, task_kwargs = mock_apply_async.call_args[0]
            send_email(*task_args, **task_kwargs)
            self.assertRedirects(response, self.success_url)
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(self.user_data['email'], mail.outbox[0].to)

    def setup_password_reset_data(self):
        """Setup data to test password resetting functionality."""
        password_reset_context = self.client.post(self.url, {'email': self.user_data['email']}).context
        token = password_reset_context['token']
        uid = password_reset_context['uid']
        url = reverse_lazy('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        return self.client.get(response.url), response.url

    def test_password_reset_confirm_form_loads_successfully(self):
        """Test if confirm password page is loading correctly."""
        if not settings.IS_EMAIL_SENDING_ENABLED:
            return
        response, _ = self.setup_password_reset_data()
        self.assertIn('form', response.context)

    def test_password_reset_confirm_successfully(self):
        """Test if password reset is working correctly."""
        if not settings.IS_EMAIL_SENDING_ENABLED:
            return
        response, url = self.setup_password_reset_data()
        new_password = 'testmynewpassword321'
        response = self.client.post(url, {'new_password1': new_password, 'new_password2': new_password})
        self.assertRedirects(response, reverse_lazy('password_reset_complete'))
        self.assertTrue(self.client.login(email=self.user_data['email'], password=new_password))


class HomePageTests(TestCase):
    """Tests for HomeView."""

    def setUp(self):
        """Set up data for testing."""
        self.url = reverse_lazy('user-home')
        self.login_url = reverse_lazy('login')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpassword',
        }
        self.user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

    def test_homepage_for_unauthenticated_user(self):
        """Test if unauthenticated user is redirected to login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(f'next={reverse(settings.LOGIN_REDIRECT_URL)}' in response.url)

    def test_homepage_for_authenticated_user(self):
        """Test if authenticated user is able to access home page."""
        self.client.login(email=self.user_data['email'], password=self.user_data['password'])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')


@override_settings(SKIP_ACTIVATION=False)
class UserActivationTests(TestCase):
    """Test different scenarios for user activation for views."""

    def setUp(self):
        """Set up test data."""
        self.login_url = reverse('login')
        self.user = User.objects.create_user('test@example.com', 'testpassword')
        self.inactive_user = User.objects.create_user('test1@example.com', 'testpassword')
        self.log_redirect_url = reverse(settings.LOGIN_REDIRECT_URL)

    @staticmethod
    def get_activation_url(user):
        """Make activation url for a user."""
        uid, token = create_uid_and_token(user, token_generator=AccountActiveTokenGenerator())
        return reverse('activate-user', args=[uid, token])

    def test_inactive_user_creation(self):
        """Test if new users are set as inactive."""
        password = 'testpassword'
        data = {'email': 'email@example.com', 'password1': password, 'password2': password}
        response = self.client.post(reverse('signup'), data=data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='email@example.com')
        self.assertFalse(user.is_active)
        self.assertTrue(user.activation_email_sent_at)

    def test_inactive_user_login(self):
        """Test if inactive user is able to access home page."""
        response = self.client.post(self.login_url, data={'email': self.user.email, 'password': 'testpassword'})
        self.assertTrue(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_authenticated)
        self.client.force_login(user=self.user)
        response = self.client.get(self.log_redirect_url)
        self.assertEqual(response.status_code, 200)

    def test_user_activation(self):
        """Test user activation."""
        response = self.client.get(self.get_activation_url(self.user))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.log_redirect_url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_resending_activation_email(self):
        """Test resending of activation email."""
        last_sent = self.inactive_user.activation_email_sent_at
        self.client.force_login(self.inactive_user)
        response = self.client.get(reverse('send-activation-email'))
        self.assertEqual(response.status_code, 302)
        self.inactive_user.refresh_from_db()
        self.assertEqual(self.inactive_user.activation_email_sent_at, last_sent)
        new_time = timezone.now() - timedelta(seconds=settings.ACTIVATION_EMAIL_RESEND_TIME + 10)
        self.inactive_user.activation_email_sent_at = new_time
        self.inactive_user.was_activated = False
        self.inactive_user.save()
        self.client.get(reverse('send-activation-email'))
        self.inactive_user.refresh_from_db()
        self.assertTrue(new_time != self.inactive_user.activation_email_sent_at)
        new_time = self.inactive_user.activation_email_sent_at
        self.client.get(reverse('send-activation-email'))
        self.inactive_user.refresh_from_db()
        self.assertTrue(new_time == self.inactive_user.activation_email_sent_at)

    @override_settings(IS_EMAIL_SENDING_ENABLED=False)
    def test_activation_email(self):
        """Test if activation email is working properly."""
        if not settings.IS_EMAIL_SENDING_ENABLED:
            return
        with patch('core.tasks.send_email.apply_async') as mock_apply_async:
            user = User.objects.create_user('example@example.com', 'testpassword')
            task_args, task_kwargs = mock_apply_async.call_args[0]
            send_email(*task_args, **task_kwargs)
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(user.email, mail.outbox[0].to)
