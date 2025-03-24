"""Views for users APIs."""
import jwt
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404, JsonResponse
from rest_framework import status,viewsets
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.decorators import authentication_classes, permission_classes

from users.api.v1.permissions import IsAuthenticatedAndActivated, IsNotAuthenticated,IsPublic
from users.api.v1.serializers import (
    ProfileSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
    RegisterUserSerializer, VerifyCodeSerializer, CompleteProfileSerializer
)
from users.emails import UserActivationEmail,VerificationTokenEmail
from users.models import UserProfile,User,VerificationToken,TemporaryToken
from users.utils import activate_user, allow_sending_activation_email, create_auth_data
from datetime import datetime, timedelta
import re
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

def generate_temp_token(user):
    payload = {
        'user_email': user.emai,
        'exp': datetime.utcnow() + timedelta(hours=24),  # Expire in 24 hours
        'temp_token': True,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    # Store the token in the database
    temp_token_instance = TemporaryToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=24)
    )
    return token


class RegisterUserView(viewsets.ViewSet):
    """Handle user registration and send verification code."""
    authentication_classes = []
    permission_classes = [AllowAny]  # Make the view public
    serializer_class = RegisterUserSerializer

    # @permission_classes([IsNotAuthenticated])   # Pass a list of permission classes
    def create(self, request):
        """Create a user and send a verification code."""
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate a random verification code and set expiration time
            token_code = f"{random.randint(100000, 999999)}"
            expiration_time = timezone.now() + timedelta(minutes=10)

            # Check if a token already exists for the user, create if not
            token, created = VerificationToken.objects.get_or_create(
                user=user,
                defaults={'code': token_code, 'expiration_time': expiration_time}
            )

            if not created:
                # If token already exists, update it
                token.code = token_code
                token.expiration_time = expiration_time
                token.save()

            user.activation_email_sent_at = timezone.now()
            user.save()

            # Send verification email
            VerificationTokenEmail().send([user.email], {"otp_code": token_code}, user=request.user)

            return Response({'message': 'Verification code sent to email'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class VerifyUserView(APIView):
    """Verify user registration with a verification code."""
    authentication_classes = []
    permission_classes = [AllowAny]  # Make the view public
    serializer_class = VerifyCodeSerializer
    def post(self, request, *args, **kwargs):
        """Verify the user using the code sent to the email."""
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Handle verification logic
            return Response({'message': 'User verified successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteUserProfileView(APIView):
    """Complete the user's profile after registration."""

    def post(self, request, *args, **kwargs):
        """Complete user profile (first name, last name, etc.)."""
        
        email = request.data.get('email')  # Get the email from the payload
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
        try:
            user = User.objects.get(email=email)  # Retrieve user by email
            if not user.was_activated:
                return Response({'error': 'unverified user'}, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CompleteProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile completed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(viewsets.ModelViewSet):
    """ViewSet for UserProfile actions."""
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    def get_object(self):
        """Get object if only user ID matches profile ID."""
        try:
            profile = super().get_object()
        except UserProfile.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND("Profile not found.")

        # Check if the requesting user is authorized to access the profile
        request_user = self.request.user
        if not request_user.is_staff and not request_user.is_superuser and profile.user != request_user:
            raise status.HTTP_404_NOT_FOUND("You do not have permission to access this profile.")

        return profile

# class SignupEmailView(APIView):
#     """Send password reset based on front-end URL setting."""
#
#     def post(self, request, *args, **kwargs):
#         """Send password reset email based on front-end URL."""
#         dta = {
#             "email": "abc@test.com"
#         }
#         serializer = SignupSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         if serializer.is_valid():
#
#         front_end_url = settings.FRONTEND_PASSWORD_RESET_URL
#         extra_email_context = {'url': ''}
#         if front_end_url:
#             extra_email_context['url'] = f'{settings.FRONTEND_BASE_URL}{front_end_url}'
#
#         serializer.save(request=request, extra_email_context=extra_email_context)
#         return Response({'status': 'OK'}, status=HTTP_200_OK)

class RequestPasswordReset(APIView):
    """Send password reset based on front-end URL setting."""

    def post(self, request, *args, **kwargs):
        """Send password reset email based on front-end URL."""
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        front_end_url = settings.FRONTEND_PASSWORD_RESET_URL
        extra_email_context = {'url': ''}
        if front_end_url:
            extra_email_context['url'] = f'{settings.FRONTEND_BASE_URL}{front_end_url}'

        serializer.save(request=request, extra_email_context=extra_email_context)
        return Response({'status': 'OK'}, status=HTTP_200_OK)


class ResetPassword(APIView):
    """Reset user's password."""

    def post(self, request, *args, **kwargs):
        """Disable CSRF for API password reset."""
        serializer = ResetPasswordSerializer(data={
            **request.data,
            'uidb64': kwargs.get('uidb64', ''),
            'token': kwargs.get('token', ''),
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'OK'}, status=HTTP_200_OK)


class ActivateUserAccount(APIView):
    """Activate a user's account."""

    def get(self, request, *args, **kwargs):
        """Activate a user using uid and token from URL."""
        was_activated, user = activate_user(kwargs.get('uidb64', ''), kwargs.get('token', ''))
        if not was_activated:
            return JsonResponse(data={'error': 'Token is invalid or expired '}, status=HTTP_400_BAD_REQUEST)

        data = create_auth_data(user)
        return JsonResponse(data=data, status=HTTP_200_OK)


class ResendActivationMail(APIView):
    """Activate a user's account."""

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Resend activation email if allowed."""
        if not allow_sending_activation_email(request.user):
            return JsonResponse(data={'error': 'Email already sent!'}, status=HTTP_400_BAD_REQUEST)

        UserActivationEmail().send([request.user.email], {}, user=request.user)
        request.user.activation_email_sent_at = timezone.now()
        request.user.save(update_fields=['activation_email_sent_at'])
        return JsonResponse(data={'msg': 'Email sent successfully'}, status=HTTP_200_OK)


class GoogleLogin(SocialLoginView):
    """Sign in with Google using API."""

    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_CALLBACK_URL
    client_class = OAuth2Client

