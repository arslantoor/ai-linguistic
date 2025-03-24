"""Forms for users app."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserChangeForm, UserCreationForm

from users.emails import ForgetPasswordEmail

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Form for creating a user."""

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']


class UserUpdateForm(UserChangeForm):
    """Form to update user."""

    password = None

    class Meta:
        model = User
        fields = ['first_name', 'last_name', ]


class CustomAuthenticationForm(AuthenticationForm):
    """Form for signing in a user."""

    class Meta:
        model = User
        fields = ['email', 'password']

    def confirm_login_allowed(self, user):
        """Allow login of inactive users."""
        pass


class CustomPasswordChangeForm(PasswordResetForm):
    """Add front end URL to email if required."""

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email,
                  html_email_template_name=None,):
        """Send a password reset email."""
        forget_password_email = ForgetPasswordEmail()
        context.pop('user')
        forget_password_email.send([to_email], context)

