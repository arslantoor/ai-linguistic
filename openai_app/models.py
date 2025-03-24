from django.db import models

# Create your models here.
from django.db import models
from pgvector.django import VectorField

class TranslationEmbedding(models.Model):
    source_text = models.TextField()
    target_text = models.TextField()
    embedding = VectorField(dimensions=1536)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Translation: {self.source_text[:50]}..."