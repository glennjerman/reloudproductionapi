from rest_framework import serializers
from api.models import User, Audio
from django.core.files.storage import default_storage
from django.urls import reverse
import os
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password')
    
    def create(self, validated_data):
        user = User(
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
class AudioSerializer(serializers.ModelSerializer):
    preview_image = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Audio
        fields = ('id', 'name', 'user', 'preview_image', 'audio')

    def get_preview_image(self, obj):
        if obj.preview_image:
            request = self.context.get('request')
            file_path = default_storage.path(obj.preview_image.name)
            url_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
            return 'https://api.reloud.xyz' + settings.MEDIA_URL + url_path
        return None
    
    def get_audio(self, obj):
        request = self.context.get('request')
        file_path = default_storage.path(obj.audio.name)
        url_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
        return 'https://api.reloud.xyz' + settings.MEDIA_URL + url_path
    


    def create(self, validated_data):
        audio = Audio(
            name=validated_data['name'],
            user=self.context['request'].user
        )
        audio.save()
        return audio