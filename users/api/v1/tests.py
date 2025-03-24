"""Tests for users APIs."""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse_lazy
from django.utils import timezone
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND
)
from rest_framework.test import APITestCase

from users.token_generators import AccountActiveTokenGenerator
from users.utils import create_uid_and_token

User = get_user_model()


class AuthenticationTests(APITestCase):
    """Test API for authentication of users."""

    def setUp(self):
        """Set up data for testing."""
        self.signup_url = reverse_lazy('users-api-list')
        self.login_url = reverse_lazy('api-login')

    def test_signup_with_valid_data(self):
        """Test user signup with valid data."""
        data = {
            'email': 'test@example.com',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'test@example.com')

    def test_signup_with_missing_email(self):
        """Test user signup with missing email."""
        data = {
            'password': 'testpassword',
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_signup_with_missmatching_passwords(self):
        """Test user signup with different passwords."""
        data = {
            'email': 'test1@example.com',
            'password': 'testpassword',
            'confirm_password': 'testpassword2',
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_signup_with_existing_email(self):
        """Test user signup with an email that already exists."""
        User.objects.create_user(
            email='test@example.com',
            password='testpassword',
        )
        data = {
            'email': 'test@example.com',
            'password': 'testpassword',
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_login_with_valid_credentials(self):
        """Test user login with valid credentials."""
        User.objects.create_user(
            email='test@example.com',
            password='testpassword',
        )
        data = {
            'email': 'test@example.com',
            'password': 'testpassword',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertIn('id', response.data['user'])

    def test_login_with_invalid_credentials(self):
        """Test user login with invalid credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertNotIn('refresh', response.data)
        self.assertNotIn('access', response.data)

    def test_signup_with_authenticated_user(self):
        """Test if signup URL is accessible to authenticated user."""
        User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        data = {
            'email': 'test@example.com',
            'password': 'testpassword',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)


class UserViewSetTest(APITestCase):
    """Test cases for UserViewSet."""

    def setUp(self):
        """Setup data for testing."""
        self.data = {
            'email': 'testuser@test.com',
            'password': 'testpassword'
        }
        self.staff_user = User.objects.create_staff(
            email='staff@staff.com',
            password='staff_password'
        )
        self.user = User.objects.create_user(email=self.data['email'], password=self.data['password'], is_active=True)
        self.user_count = 2
        self.user_detail_url_name = 'users-api-detail'

    def _get_url(self, user_id, **kwargs):
        """Create url with user id."""
        return reverse_lazy(self.user_detail_url_name, kwargs={'pk': user_id, **kwargs})

    def test_unauthorized_access(self):
        """Test if profile view is accessible without signing in."""
        response = self.client.get(self._get_url(self.user.id))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_user_detail(self):
        """Test user detail url."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self._get_url(self.user.id))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_user_detail_for_other_user(self):
        """Test if a user is able to access other user's details."""
        another_user = User.objects.create_user(email='anotheruser@test.com', password='anotherpassword')
        self.client.force_authenticate(user=another_user)
        response = self.client.get(self._get_url(self.user.id))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_update_user(self):
        """Test user successful update."""
        self.client.force_authenticate(user=self.staff_user)
        data = {'first_name': 'updateduser', 'email': 'some@test.com'}
        response = self.client.patch(self._get_url(self.user.id), data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data['first_name'], data['first_name'])
        self.assertEqual(response.data['email'], self.user.email)

    def test_list_users_for_staff(self):
        """Test if staff is able to list all users."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(reverse_lazy('users-api-list'))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.data), self.user_count)

    def test_list_users_for_staff_with_profile(self):
        """Test if staff is able to list all users."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'{reverse_lazy("users-api-list")}?profile=true')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.data), self.user_count)
        self.assertTrue('profile' in response.data[0])

    def test_list_users_for_normal_user(self):
        """Test if normal user is able to list all users."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse_lazy('users-api-list'))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)


class ProfileViewTest(APITestCase):
    """Test cases for ProfileView."""

    def setUp(self):
        """Setup data for testing."""
        self.data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        self.user = User.objects.create_user(
            email=self.data['email'],
            password=self.data['password'],
            is_active=True,
        )
        self.staff_user = User.objects.create_staff(
            email='staff@staff.com',
            password='passwordForSomeStaffMember'
        )
        self.random_user = User.objects.create_user(email='user@user.com', password='somerandmuser123')
        self.user_count = 3
        self.login_url = reverse_lazy('api-login')
        self.url_name = 'get-profile'

    def _get_profile_url(self, user_id):
        """Get profile URL."""
        return reverse_lazy(self.url_name, kwargs={'pk': user_id})

    def test_unauthorized_access(self):
        """Test if profile view is accessible without signing in."""
        response = self.client.get(self._get_profile_url(self.user.id))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authorized_access(self):
        """Test if profile view is accessible after signing in."""
        self.client.force_authenticate(self.staff_user)
        response = self.client.get(self._get_profile_url(self.user.profile.id))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertEqual(self.user.profile.id, response.data['id'])

    def test_profile_access_of_another_user(self):
        """Test if a user is able to access some other user's profile."""
        self.client.force_authenticate(self.user)
        response = self.client.get(self._get_profile_url(self.random_user.id))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_staff_access_to_profile(self):
        """Test if a staff user is able to access other user profiles."""
        self.client.force_authenticate(self.staff_user)
        response = self.client.get(self._get_profile_url(self.random_user.profile.id))
        self.assertEqual(response.status_code, HTTP_200_OK)


@override_settings(SKIP_ACTIVATION=False)
class ActivationTests(APITestCase):
    """Test cases for inactive users."""

    def setUp(self):
        """Set up test data."""
        self.login_url = reverse_lazy('api-login')
        self.user = User.objects.create_user('test@example.com', 'testpassword')
        self.inactive_user = User.objects.create_user('test1@example.com', 'testpassword')

    @staticmethod
    def get_activation_url(user):
        """Make activation url for a user."""
        uid, token = create_uid_and_token(user, token_generator=AccountActiveTokenGenerator())
        return reverse_lazy('activate-user-api', args=[uid, token])

    def test_inactive_user_creation(self):
        """Test if new users are set as inactive."""
        password = 'testpassword'
        data = {'email': 'email@example.com', 'password': password, 'confirm_password': password}
        response = self.client.post(reverse_lazy('users-api-list'), data=data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        user = User.objects.get(email='email@example.com')
        self.assertFalse(user.is_active)
        self.assertTrue(user.activation_email_sent_at)

    def test_inactive_user_login(self):
        """Test if inactive user is able to retrieve his detail.."""
        response = self.client.post(self.login_url, data={'email': self.user.email, 'password': 'testpassword'})
        self.assertTrue(response.status_code, HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_authenticated)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse_lazy('users-api-detail', kwargs={'pk': self.user.id}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_user_activation(self):
        """Test user activation."""
        response = self.client.get(self.get_activation_url(self.user))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_resending_activation_email(self):
        """Test resending of activation email."""
        get_activation_email_url = lambda x: reverse_lazy('send-activation-email-api', kwargs={'pk': x})

        last_sent = self.inactive_user.activation_email_sent_at
        self.client.force_authenticate(self.inactive_user)
        response = self.client.get(get_activation_email_url(self.inactive_user.id))
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.inactive_user.refresh_from_db()
        self.assertEqual(self.inactive_user.activation_email_sent_at, last_sent)
        new_time = timezone.now() - timedelta(seconds=settings.ACTIVATION_EMAIL_RESEND_TIME + 10)
        self.inactive_user.activation_email_sent_at = new_time
        self.inactive_user.was_activated = False
        self.inactive_user.save()
        self.client.get(get_activation_email_url(self.inactive_user.id))
        self.inactive_user.refresh_from_db()
        self.assertTrue(new_time != self.inactive_user.activation_email_sent_at)
        new_time = self.inactive_user.activation_email_sent_at
        self.client.get(get_activation_email_url(self.inactive_user.id))
        self.inactive_user.refresh_from_db()
        self.assertTrue(new_time == self.inactive_user.activation_email_sent_at)
