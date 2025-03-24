import uuid
from django.db import models
from django.conf import settings  # Import settings to use AUTH_USER_MODEL
from pgvector.django import VectorField
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    client_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use settings.AUTH_USER_MODEL instead of User
        on_delete=models.CASCADE,
        related_name="projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]  # Newest first

    def __str__(self):
        return self.name


# file storage as vector
# Define supported file types
FILE_TYPE_CHOICES = [
    ("xliff", "XLIFF"),
    ("sdlxliff", "SDLXLIFF"),
    ("dmx", "DMX"),
    ("docx", "DOCX"),
    ("pptx", "PPTX"),
    ("xlsx", "XLSX"),
]

LANGUAGE_CHOICES = [
    ("monolingual", "Monolingual"),
    ("bilingual", "Bilingual"),
]

class ProjectFile(models.Model):
    """Model for handling multiple file uploads for a project."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="uploaded_files")
    openai_file_id = models.CharField(max_length=255, unique=True)  # Store OpenAI's file ID
    vector_store_id = models.CharField(max_length=255, unique=False,null=True)  # Store OpenAI's file ID
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

class UploadedFile(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="uploads/")  # ✅ Store file locally
    openai_file_id = models.CharField(max_length=100, null=True, blank=True)  # ✅ OpenAI file ID
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name