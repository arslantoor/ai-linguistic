"""utility methods for users."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class LoggedInTests(TestCase):
    """Base test case class for logging in users."""

    urls = [
        {'mehod': 'post', 'path_name': '', 'data': {}}
    ]

    def setUp(self, **kwargs):
        """Create user for login."""
        self.user_data = {
            'email': 'test_login_user@example.com',
            'password': 'test@00912'
        }
        self.user = User.objects.create_user(self.user_data['email'], self.user_data['password'])
        if kwargs.get('test_urls', True):
            self.start_test_for_urls()

    def start_test_for_urls(self):
        """Test if mentioned URLs are accessible without login."""
        login_url = reverse('login')
        for url in self.urls:
            path = reverse(url['path_name'])
            if url['method'] == 'post':
                response = self.client.post(path, data=url['data'])
            else:
                response = self.client.get(path)

            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_url in response.url)

    def login_user_for_views(self):
        """Log in a user to test views that requires logged in users."""
        self.client.login(email=self.user_data['email'], password=self.user_data['password'])
