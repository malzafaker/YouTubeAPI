from rest_framework import serializers

from apps.youtube.models import YouTubeVideo


class YouTubeVideoSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = YouTubeVideo
        fields = ('id', 'file', 'title', 'description')

