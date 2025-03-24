from django.test import TestCase
from openai.services.services import OpenAIService

class OpenAIServiceTest(TestCase):
    def test_generate_response(self):
        ai_service = OpenAIService()
        response = ai_service.generate_response([{"role": "user", "content": "Hello"}])
        self.assertIsInstance(response, str)
