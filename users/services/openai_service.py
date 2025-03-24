import openai
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    """Handles interactions with OpenAI API"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        openai.api_key = self.api_key

    def generate_response(self, messages: list, model="gpt-4"):
        """Sends a request to OpenAI API and returns a response"""
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
            )
            return response["choices"][0]["message"]["content"]
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None
