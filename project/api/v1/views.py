import os

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions,status
import logging

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from project.models import Project, ProjectFile, UploadedFile
from .serializers import ProjectSerializer, ProjectFileSerializer, FileUploadSerializer, UploadSerializer, \
    UploadedFileSerializer, FetchFileSerializer
from concurrent.futures import ThreadPoolExecutor
from openai_app.services.services import OpenAIService  # Import OpenAIService

logger = logging.getLogger(__name__)
# Allowed file extensions
ALLOWED_EXTENSIONS = {"xliff", "sdlxliff", "dmx", "docx", "pptx", "xlsx"}

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can access

    def create(self, serializer):
        serializer.save(created_by=self.request.user)  # Assign current user as creator


class UploadFileViewSet(viewsets.ViewSet):
    serializer_class = ProjectFileSerializer

    @action(detail=False, methods=['post'])
    def file(self, request, *args, **kwargs):
        """Handles storing file metadata after media upload API call"""
        try:
            project_id = request.data.get("Project")  # Fetch Project UUID
            vector_store_id = request.data.get("vector_store_id")
            files_data = request.data.get("files", [])

            if not project_id or not files_data:
                return Response({"error": "Project ID and files list are required."},
                                status=status.HTTP_400_BAD_REQUEST)

            project = get_object_or_404(Project, id=project_id)  # Fetch project instance
            current_user = request.user  # Get logged-in user

            project_files = [
                ProjectFile(
                    project=project,
                    uploaded_by=current_user,
                    openai_file_id=file_data.get("openai_file_id"),
                    vector_store_id=vector_store_id,  # Same for all files
                    file_name=file_data.get("filename"),
                    file_type=file_data.get("file_type"),
                )
                for file_data in files_data
                if file_data.get("filename") and file_data.get("openai_file_id")  # Ensure required fields exist
            ]

            if not project_files:
                return Response({"error": "No valid file entries found."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Bulk insert in a single query
            ProjectFile.objects.bulk_create(project_files)

            return Response({"message": "Files metadata stored successfully."},
                            status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Something went wrong: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MediaUpload(viewsets.ViewSet):
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = UploadSerializer

    @action(detail=False, methods=['post'])
    def media(self, request, *args, **kwargs):
        files = request.FILES.getlist("file")  # Get multiple files
        openai_service = OpenAIService()

        if not files:
            return Response({"error": "At least one file is required"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_files = []  # Store results

        def process_file(file):
            file_path = f"/tmp/{file.name}"
            with open(file_path, "wb") as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            try:
                openai_file = openai_service.upload_file(file_path)
                os.remove(file_path)
                # Convert VectorStoreFile object to dictionary# Cleanup
                openai_file_dict = {
                    "id": openai_file.id,
                    "created_at": openai_file.created_at,
                    "last_error": openai_file.last_error,
                    "object": openai_file.object,
                    "status": openai_file.status,
                    "usage_bytes": openai_file.usage_bytes,
                    "vector_store_id": openai_file.vector_store_id,
                }
                return {"filename": file.name, "data": openai_file_dict}
            except Exception as e:
                return {"filename": file.name, "error": str(e)}

        # Execute parallel file uploads
        with ThreadPoolExecutor() as executor:

            uploaded_files = list(executor.map(process_file, files))

        return Response({"data": uploaded_files}, status=status.HTTP_201_CREATED)

class FileFetchView(viewsets.ModelViewSet):
    # queryset = ProjectFile.objects.all()
    serializer_class = FetchFileSerializer
    def list(self, request):
        """Fetch all ProjectFile records"""
        project_files = ProjectFile.objects.all()
        serializer = FetchFileSerializer(project_files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Fetch a ProjectFile record by UUID"""
        project_file = get_object_or_404(ProjectFile, id=pk)
        serializer = FetchFileSerializer(project_file)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_by_project(self, request, project_id):
        """Fetch all ProjectFile records by project_id"""
        project_files = ProjectFile.objects.filter(project_id=project_id)
        if not project_files.exists():
            return Response({"error": "No files found for this project."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = FetchFileSerializer(project_files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)