from rest_framework import serializers
from project.models import Project,ProjectFile,UploadedFile


class ProjectSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = Project
        fields = "__all__"

class ProjectFileSerializer(serializers.ModelSerializer):
    """Serializer for uploaded file metadata."""
    files = serializers.ListField(
        child=serializers.URLField(),  # ✅ Allow multiple files
        write_only=True
    )
    class Meta:
        model = ProjectFile
        fields = ["id", "project", "openai_file_id", "vector_store_id","file_name", "file_type", "created_at",'files']
        read_only_fields = ['id',]

    def validate_files(self, files):
        """Check if file extensions are allowed"""
        allowed_extensions = {"xliff", "sdlxliff", "dmx", "docx", "pptx", "xlsx"}
        for file in files:
            ext = file.name.split(".")[-1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(f"Invalid file type: {file.name}")
        return files


class FileUploadSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.FileField(),  # ✅ Allow multiple files
        write_only=True
    )

    class Meta:
        model = UploadedFile
        fields = ["files"]

    def validate_files(self, files):
        """Check if file extensions are allowed"""
        allowed_extensions = {"xliff", "sdlxliff", "dmx", "docx", "pptx", "xlsx"}
        for file in files:
            ext = file.name.split(".")[-1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(f"Invalid file type: {file.name}")
        return files

from rest_framework.serializers import Serializer,FilePathField,SlugField,FileField


class UploadSerializer(Serializer):
    files = serializers.FileField(),
    class Meta:
        model: UploadedFile
        fields = ['files']

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ["id", "file_name", "openai_file_id", "uploaded_at"]

class FetchFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = ["id", "project", "openai_file_id", "vector_store_id","file_name", "file_type", "created_at"]