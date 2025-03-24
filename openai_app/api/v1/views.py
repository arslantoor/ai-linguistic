from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status, permissions
from openai_app.services.services import OpenAIService
from .serializers import OpenAIRequestSerializer


class OpenAIChatViewSet(viewsets.ViewSet):
    """ViewSet for handling OpenAI API chat requests"""

    permission_classes = [permissions.IsAuthenticated]  # ✅ Secure API
    serializer_class = OpenAIRequestSerializer
    def create(self, request):
        """Handles AI chat processing"""
        serializer = OpenAIRequestSerializer(data=request.data)
        if serializer.is_valid():
            ai_service = OpenAIService()
            response_text = ai_service.generate_response(serializer.validated_data["messages"])
            if response_text:
                return Response({"response": response_text}, status=status.HTTP_200_OK)
            return Response({"error": "AI service unavailable"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)