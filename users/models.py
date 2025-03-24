from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import random
import string
from django.core.mail import send_mail
import datetime

class CustomUserManager(BaseUserManager):
    """Custom user manager for using email instead of username."""

    def create_user(self, email, password=None, first_name='', last_name='', date_of_birth=None, is_active=settings.SKIP_ACTIVATION):
        """Create user with given params."""
        if not email:
            raise ValueError('Users must have an email address')

        # Validate that date_of_birth is provided if it's not empty
        if date_of_birth and not isinstance(date_of_birth, datetime.date):
            raise ValueError('Invalid date of birth format')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            was_activated=is_active
        )
        if password:  # Set password only if it's provided
            user.set_password(password)
        user.save(using=self._db)

        return user

    def create_staff(self, email, password=None):
        """Create staff with given params."""
        user = self.create_user(email=email, password=password)
        user.is_staff = user.is_active = user.was_activated = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name='', last_name='', password=None,date_of_birth=None):
        """
        Create and save a superuser with the given email, first name, last name, and password.
        """
        # Validate that date_of_birth is provided if it's not empty
        if date_of_birth and not isinstance(date_of_birth, datetime.date):
            raise ValueError('Invalid date of birth format')
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    """Custom user model for using email instead of username."""

    username = None  # Removing username
    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    activation_email_sent_at = models.DateTimeField(null=True, blank=True)
    was_activated = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'date_of_birth']

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        """Send activation email and create user profile."""
        if self.pk:
            return super().save(*args, **kwargs)

        is_social_account = getattr(self, 'is_social_account', False)
        is_staff_or_superuser = self.is_staff or self.is_superuser
        self.is_active = is_social_account or is_staff_or_superuser or settings.SKIP_ACTIVATION
        self.was_activated = self.is_active
        super().save(*args, **kwargs)


class VerificationToken(models.Model):
    """Model to store email verification codes."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expiration_time = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return timezone.now() > self.expiration_time

class TemporaryToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, default="active")

    def is_expired(self):
        return timezone.now() > self.expires_at

    def expire(self):
        self.status = "expired"
        self.save()


class UserProfile(models.Model):
    """User profile for our custom user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    def __str__(self):
        """String representation of model."""
        return self.user.email
