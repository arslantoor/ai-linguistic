"""URLs for user app."""

from django.urls import include, path

urlpatterns = [
    # SSO URLs
    path('accounts/', include('allauth.urls'))
]
