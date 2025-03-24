"""URLs for project APIs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet, UploadFileViewSet, MediaUpload, FileFetchView

router = DefaultRouter()

router.register(r'', ProjectViewSet, basename='project', )
router.register(r'upload', UploadFileViewSet, basename='uploadfile')
router.register(r"media", MediaUpload, basename="media")
# router.register(r"files", FileFetchView, basename="list-all-media")

urlpatterns = [
    path('files/', FileFetchView.as_view({'get': 'list'}), name='all-files'),
    path('files/<uuid:pk>/', FileFetchView.as_view({'get': 'retrieve'}), name='file-detail'),
    path('', include(router.urls)), ]
