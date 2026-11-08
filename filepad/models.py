from django.db import models
import os
import uuid


def user_directory_path(instance, filename):
    """Store files under a random vault UUID, never a password-derived ID."""
    return os.path.join(
        'filepad',
        str(instance.user_space.vault_uuid),
        filename
    )


class UserSpace(models.Model):
    """A vault identified by a secret lookup ID and verified using Argon2."""

    vault_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    lookup_id = models.CharField(
        max_length=64,
        unique=True,
    )

    password_verifier = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_accessed']

    def __str__(self):
        return f"Vault: {self.vault_uuid}"


class UploadedFile(models.Model):
    """Metadata for files stored in a user's vault."""

    user_space = models.ForeignKey(
        UserSpace,
        on_delete=models.CASCADE,
        related_name='files'
    )

    file = models.FileField(upload_to=user_directory_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return (
            f"{self.original_filename} - "
            f"{self.user_space.vault_uuid}"
        )

    def delete(self, *args, **kwargs):
        """Delete the associated stored file when deleting its record."""
        if self.file:
            try:
                self.file.delete(save=False)
            except Exception:
                pass

        super().delete(*args, **kwargs)

    @property
    def file_url(self):
        return self.file.url if self.file else None
