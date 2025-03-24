import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from users.models import VerificationToken

class VerificationTokenService:
    @staticmethod
    def generate_otp(user):
        """ Generate otp code """
        token,created = VerificationToken.objects.get_or_create(user=user)
        token.code = ''.join(random.choices(string.digits, k=6))  # 6-digit code
        token.expiration_time = timezone.now() + timedelta(minutes=15)  # Expires in 15 minutes
        token.save()
        return token
    @staticmethod
    def send_token_email(self,user):
        """Send the verification token via email."""
        