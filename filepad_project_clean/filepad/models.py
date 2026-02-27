from django.db import models
import os


def user_directory_path(instance, filename):
    """Generate upload path: filepad/{user_hash}/{filename}"""
    return os.path.join('filepad', instance.user_space.user_hash, filename)


class UserSpace(models.Model):
    """User space identified by password hash"""
    user_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_accessed']

    def __str__(self):
        return f"UserSpace: {self.user_hash[:10]}..."


class UploadedFile(models.Model):
    """Uploaded file metadata"""
    user_space = models.ForeignKey(UserSpace, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=user_directory_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename} - {self.user_space.user_hash[:10]}..."

    def delete(self, *args, **kwargs):
        """Delete file from storage when record is deleted"""
        if self.file:
            try:
                self.file.delete(save=False)
            except Exception:
                pass
        super().delete(*args, **kwargs)

    @property
    def file_url(self):
        """Get file URL"""
        return self.file.url if self.file else None
