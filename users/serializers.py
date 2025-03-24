from rest_framework import serializers

class OpenAIRequestSerializer(serializers.Serializer):
    messages = serializers.ListField(child=serializers.DictField())
