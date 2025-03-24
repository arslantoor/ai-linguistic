"""URLs for open APIs."""
from django.urls import path,include
from rest_framework.routers import DefaultRouter

from openai_app.api.v1.views import OpenAIChatViewSet
router = DefaultRouter()
router.register(r'chat', OpenAIChatViewSet, basename='chat')

urlpatterns = [
    path('', include(router.urls)),
]
# urlpatterns = [path('chat/', OpenAIChatViewSet, name='api-login'), ] + router.urls
