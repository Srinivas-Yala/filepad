from rest_framework import serializers
from .models import UserSpace, UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for uploaded files."""

    class Meta:
        model = UploadedFile
        fields = [
            'id',
            'original_filename',
            'file_size',
            'file_type',
            'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads."""

    file = serializers.FileField()
    password = serializers.CharField(write_only=True)

    def validate_file(self, value):
        """Validate file size (100MB limit)."""

        if value.size > 100 * 1024 * 1024:
            raise serializers.ValidationError(
                "File size cannot exceed 100MB"
            )

        return value


class UserSpaceSerializer(serializers.ModelSerializer):
    """Serializer for user vaults."""

    files = UploadedFileSerializer(many=True, read_only=True)
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = UserSpace
        fields = [
            'id',
            'created_at',
            'last_accessed',
            'files',
            'file_count'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'last_accessed'
        ]

    def get_file_count(self, obj):
        return obj.files.count()
