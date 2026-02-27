from django.contrib import admin
from .models import UserSpace, UploadedFile


@admin.register(UserSpace)
class UserSpaceAdmin(admin.ModelAdmin):
    list_display = ['user_hash', 'created_at', 'last_accessed', 'file_count']
    search_fields = ['user_hash']
    readonly_fields = ['user_hash', 'created_at', 'last_accessed']
    
    def file_count(self, obj):
        return obj.files.count()
    file_count.short_description = 'Files'


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'user_space', 'file_size', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['original_filename', 'user_space__user_hash']
    readonly_fields = ['uploaded_at']
