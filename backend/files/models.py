from django.db import models
from django.conf import settings


class UploadedFile(models.Model):
    """A file uploaded to the platform, ready for distribution."""
    name = models.CharField(max_length=255)
    size = models.PositiveIntegerField(default=0)
    # Relative path under MEDIA_ROOT
    path = models.CharField(max_length=512)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FileTransfer(models.Model):
    """A file-distribution run: send a local upload or a remote dir to many hosts."""
    KIND_CHOICES = [('upload', 'Local upload'), ('remote', 'Remote directory')]
    STATUS_CHOICES = [('running', 'Running'), ('success', 'Success'),
                      ('partial', 'Partial'), ('failed', 'Failed')]
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    # For kind=upload: reference to UploadedFile. For kind=remote: source path.
    uploaded_file = models.ForeignKey(UploadedFile, null=True, blank=True, on_delete=models.SET_NULL)
    source_path = models.CharField(max_length=1024, blank=True)
    target_path = models.CharField(max_length=1024)
    host_ids = models.JSONField(default=list)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='running')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Transfer {self.pk}'


class FileTransferResult(models.Model):
    transfer = models.ForeignKey(FileTransfer, related_name='results', on_delete=models.CASCADE)
    host_id = models.PositiveIntegerField()
    host_name = models.CharField(max_length=128)
    status = models.CharField(max_length=16, default='success')
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
