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
        """Uploads a file to OpenAI for fine-tuning or assistant processing"""
        try:
            with open(file_path, "rb") as file:
                response = self.client.files.create(file=file, purpose="user_data")
                vector_store_file = self.client.vector_stores.files.create(
                    vector_store_id="vs_67d4d17ccbe481918f32903175bb52b4",
                    file_id=response.id
                )
            return vector_store_file # Return file ID
        except Exception as e:
            logger.error(f"OpenAI File Upload Error: {e}")
            return None

    def get_file_content(self, file_id):
        """Fetch file content from OpenAI"""
        response = self.client.files.content(file_id)
        return response.content
