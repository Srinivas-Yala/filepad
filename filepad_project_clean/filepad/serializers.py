from rest_framework import serializers
from .models import UserSpace, UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for uploaded files"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedFile
        fields = ['id', 'original_filename', 'file_size', 'file_type', 'uploaded_at', 'file_url']
        read_only_fields = ['id', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload"""
    file = serializers.FileField()
    password = serializers.CharField(write_only=True)

    def validate_file(self, value):
        """Validate file size (10MB limit)"""
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        return value


class UserSpaceSerializer(serializers.ModelSerializer):
    """Serializer for user space"""
    files = UploadedFileSerializer(many=True, read_only=True)
    file_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSpace
        fields = ['id', 'user_hash', 'created_at', 'last_accessed', 'files', 'file_count']
        read_only_fields = ['id', 'user_hash', 'created_at', 'last_accessed']

    def get_file_count(self, obj):
        return obj.files.count()
