"""Serializers for users APIs."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.emails import ForgetPasswordEmail
from users.models import UserProfile,User as Users,VerificationToken
from users.utils import check_token, create_uid_and_token, get_user_from_uidb64

User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']  # Add required fields
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        email = validated_data['email']
        user, created = User.objects.get_or_create(email=email)
        return user


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')
        try:
            user = User.objects.get(email=email)
            token = VerificationToken.objects.get(user=user, code=code)
            if token.is_expired():
                raise serializers.ValidationError("The verification code has expired.")
        except (User.DoesNotExist, VerificationToken.DoesNotExist):
            raise serializers.ValidationError("Invalid email or verification code.")
        return data

    def save(self, **kwargs):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        user.is_active = True
        user.was_activated = True
        user.save()
        VerificationToken.objects.filter(user=user).delete()
        return user


class CompleteProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email','first_name', 'last_name', 'date_of_birth', 'password']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.set_password(validated_data['password'])
        instance.save()
        return instance
    
class ProfileSerializer(serializers.ModelSerializer):
    """Display User information."""

    class Meta:
        model = User
        fields = ['id','email', 'first_name', 'last_name','is_active']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for handling user actions."""

    password = serializers.CharField(required=True, validators=[validate_password], write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    profile = None

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id', 'is_active']

    def __init__(self, *args, **kwargs):
        """Add profile field if kwarg sent."""
        if kwargs.get('context', {}).pop('profile', False):
            self._declared_fields['profile'] = ProfileSerializer()
            self.Meta.fields.append('profile')
        super(UserSerializer, self).__init__(*args, **kwargs)

    def get_fields(self):
        """Set email field as read only when updating."""
        fields = super().get_fields()
        request = self.context.get('request', None)

        if request and self.instance:
            fields['email'].read_only = True

        return fields

    def validate(self, attrs):
        """Check if passwords match."""
        attrs = super().validate(attrs)
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({'password': 'Password fields didn\'t match.'})

        return attrs

    def create(self, validated_data):
        """Create user with all validated data."""
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update user instance."""
        profile_data = validated_data.pop('profile', None)
        if profile_data:
            profile_serializer = self.fields['profile']
            profile_instance = instance.profile
            updated_profile = profile_serializer.update(profile_instance, profile_data)
            validated_data['user'] = updated_profile

        return super().update(instance, validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """Serializer for logging in user."""

    def validate(self, attrs):
        """Add user data after validation."""
        data = super(LoginSerializer, self).validate(attrs)
        data.update({
            'user': UserSerializer(self.user).data
        })
        return data


class RequestPasswordResetSerializer(serializers.Serializer):
    """Serializer for reset password request."""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Check if user with this email exists."""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')

        if not user.is_active:
            raise serializers.ValidationError('User is inactive.')

        self.user = user
        return value

    def send_mail(self, context, to_email):
        """Send a password reset email."""
        forget_password_email = ForgetPasswordEmail()
        forget_password_email.send([to_email], context)

    def save(
        self,
        domain_override=None,
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        """Generate a one-use only link for resetting password and send it to the user."""
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        email_field_name = User.get_email_field_name()
        user_email = getattr(self.user, email_field_name)
        uid, token = create_uid_and_token(self.user, token_generator=token_generator)
        context = {
            'email': user_email,
            'domain': domain,
            'site_name': site_name,
            'uid': uid,
            'token': token,
            'protocol': 'https' if use_https else 'http',
            **(extra_email_context or {}),
        }
        self.send_mail(context, user_email)


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password."""

    uidb64 = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(validators=[validate_password], write_only=True)

    def validate(self, attrs):
        """Validate token and user."""
        uidb64 = attrs.get('uidb64')
        token = attrs.get('token')

        try:
            user = get_user_from_uidb64(uidb64)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Invalid reset link.')

        if not check_token(user, token):
            raise serializers.ValidationError('Invalid reset link.')

        attrs['user'] = user
        return attrs

    def save(self, commit=True):
        """Update password."""
        password = self.validated_data['password']
        user = self.validated_data['user']
        user.set_password(password)
        if commit:
            user.save()
        return user

# open ai services
class OpenAIRequestSerializer(serializers.Serializer):
    messages = serializers.ListField(child=serializers.DictField())
