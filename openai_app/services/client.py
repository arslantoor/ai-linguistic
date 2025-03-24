
from django.conf import settings
from openai import OpenAI


class OpenAIClient:
    """Singleton class to manage OpenAI client"""

    _client = None  # Cache instance

    @classmethod
    def get_client(cls):
        """Returns a singleton instance of OpenAI client."""
        if cls._client is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is missing. Check environment variables.")
            cls._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return cls._client
