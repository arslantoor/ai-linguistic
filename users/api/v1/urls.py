"""URLs for users APIs."""

from django.urls import path,include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.api.v1.views import (
    ActivateUserAccount,
    GoogleLogin,
    ProfileView,
    RequestPasswordReset,
    ResendActivationMail,
    ResetPassword,
    RegisterUserView,
    VerifyUserView,
    CompleteUserProfileView
)

router = DefaultRouter()
router.register(r'register', RegisterUserView, basename='register')
router.register(r'profile', ProfileView, basename='user-profile')
urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='api-login'),
	path('verify/', VerifyUserView.as_view(), name='user-verify'),
    path('activate/<uidb64>/<token>/', ActivateUserAccount.as_view(), name='activate-user-api'),
    path('', include(router.urls)),  # Include router URLs
] + router.urls
