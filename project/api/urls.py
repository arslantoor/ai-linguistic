"""URLs for users APIs."""

from django.urls import include, path

urlpatterns = [
    path('v1/project/', include('project.api.v1.urls')),
]