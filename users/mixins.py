"""Mixins related to users."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class LoginRequired(LoginRequiredMixin):
    """Log in required class to stop repetition in base classes."""

    login_url = reverse_lazy('login')


class HasUserSignedAllAgreementsMixin(AccessMixin):
    """Allow URls to be accessible to activated users only."""

    redirect_url = reverse_lazy('agreements')

    def dispatch(self, request, *args, **kwargs):
        """Allow access to views for only activated users."""
        if settings.IS_TERMS_APP_ACTIVATED and not request.user.profile.has_signed_all_terms:
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class IsAuthenticatedAndActivated(AccessMixin):
    """Allow URls to be accessible to activated users only."""

    redirect_url = reverse_lazy(settings.LOGIN_REDIRECT_URL)
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        """Allow access to views for only activated users."""
        user = request.user
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user.is_active and self.redirect_url != request.path:
            messages.warning(request, 'You need to activate your account first!')
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)
