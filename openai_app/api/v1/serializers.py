from rest_framework import serializers

class OpenAIRequestSerializer(serializers.Serializer):
    """Validates OpenAI request payload"""
    messages = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
