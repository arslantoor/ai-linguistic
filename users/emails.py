"""Emails required for users."""

from django.conf import settings
from django.urls import reverse_lazy

from users.constants import PASSWORD_RESET_EMAIL_HTML_TEMPLATE, PASSWORD_RESET_EMAIL_SUBJECT_TEMPLATE
from users.token_generators import AccountActiveTokenGenerator
from users.utils import create_uid_and_token
from core.email import BaseEmailMessage


class ForgetPasswordEmail(BaseEmailMessage):
    """Class to send password reset emails."""

    html_body_template_name = PASSWORD_RESET_EMAIL_HTML_TEMPLATE
    subject = PASSWORD_RESET_EMAIL_SUBJECT_TEMPLATE


class UserActivationEmail(BaseEmailMessage):
    """Send activation link to user."""

    html_body_template_name = 'emails/activation_email.html'
    subject = 'Activate your account'

    def _serialize_data(self, recipients, context, *args, **kwargs):
        """Create URL for activation."""
        user = kwargs.get('user', None)
        uid, token = create_uid_and_token(user, token_generator=AccountActiveTokenGenerator())

        if settings.FRONT_END_ACTIVATION_URL:
            context['url'] = f'{settings.FRONTEND_BASE_URL}{settings.FRONT_END_ACTIVATION_URL}/{uid}/{token}'
        else:
            context['url'] = f'{settings.BASE_URL}{reverse_lazy("activate-user-api", args=[uid, token])}'

        return super(UserActivationEmail, self)._serialize_data(recipients, context, *args, **kwargs)

class VerificationTokenEmail(BaseEmailMessage):
    """Send activation link to user."""

    html_body_template_name = 'emails/verification_token_email.html'
    subject = 'Activate your account'

    def _serialize_data(self, recipients, context, *args, **kwargs):

        """Create URL for activation."""

        context['code'] = context['otp_code']
        return super(VerificationTokenEmail, self)._serialize_data(recipients, context, *args, **kwargs)


class ContactUsEmail(BaseEmailMessage):
    """Send email to the receiving address of contact form."""

    def __init__(self, subject, body):
        """Initialize subject and body from dynamic string."""
        self.subject = subject
        self.body_str = body
