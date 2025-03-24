"""URLs for users APIs."""

from django.urls import include, path

urlpatterns = [
    path('v1/openai/', include('openai_app.api.v1.urls')),
]
