"""URLs for users APIs."""

from django.urls import include, path

urlpatterns = [
    path('v1/users/', include('users.api.v1.urls')),
]
