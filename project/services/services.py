import logging
from .client import OpenAIClient

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service class for handling OpenAI API calls"""

    def __init__(self):
        self.client = OpenAIClient.get_client()  # Get the singleton client

    def generate_response(self, messages):
        """Handles API calls to OpenAI and returns responses"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def upload_file(self, file_path):
        """Uploads a file to OpenAI's vector storage for Assistants API."""
        try:
            with open(file_path, "rb") as file:
                response = self.client.files.create(
                    file=file,
                    purpose="assistants"  # This stores it in OpenAI’s vector storage
                )
            return response.id  # Return the file ID
        except Exception as e:
            logger.error(f"OpenAI File Upload Error: {e}")
            return None