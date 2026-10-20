from django.db import models
from django.conf import settings


class App(models.Model):
    """An application to be released."""
    MODE_CHOICES = [('normal', 'Normal'), ('custom', 'Custom')]
    name = models.CharField(max_length=128, unique=True)
    mode = models.CharField(max_length=16, choices=MODE_CHOICES, default='normal')
    # For normal mode: repository + build config
    repo_url = models.CharField(max_length=512, blank=True)
    repo_branch = models.CharField(max_length=128, default='main')
    build_command = models.CharField(max_length=512, blank=True)
    # For custom mode: a shell script executed on target hosts
    deploy_script = models.TextField(blank=True)
    # Target hosts
    host_ids = models.JSONField(default=list)
    # Deploy path (normal mode copies built artifacts here)
    target_path = models.CharField(max_length=1024, blank=True)
    # Grayscale / compensation config
    grayscale_enabled = models.BooleanField(default=False)
    grayscale_percent = models.PositiveIntegerField(default=100)
    # Build/release separation
    build_separate = models.BooleanField(default=False)
    # Approval required
    approval_required = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Release(models.Model):
    """A release request / execution."""
    STATUS_CHOICES = [('pending', 'Pending'), ('building', 'Building'),
                      ('wait_approval', 'Waiting Approval'), ('releasing', 'Releasing'),
                      ('success', 'Success'), ('failed', 'Failed'),
                      ('rolled_back', 'Rolled Back'), ('cancelled', 'Cancelled')]
    app = models.ForeignKey(App, related_name='releases', on_delete=models.CASCADE)
    version = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # Scheduled release
    schedule_at = models.DateTimeField(null=True, blank=True)
    # Build output / log
    build_log = models.TextField(blank=True)
    release_log = models.TextField(blank=True)
    # Grayscale percent applied
    grayscale = models.PositiveIntegerField(default=100)
    # Webhook auto-release
    webhook_token = models.CharField(max_length=128, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.app.name} {self.version}'


class ReleaseApproval(models.Model):
    release = models.ForeignKey(Release, related_name='approvals', on_delete=models.CASCADE)
    decision = models.CharField(max_length=16)  # approved/rejected
    comment = models.CharField(max_length=500, blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    decided_at = models.DateTimeField(auto_now_add=True)


class ReleaseResult(models.Model):
    release = models.ForeignKey(Release, related_name='results', on_delete=models.CASCADE)
    host_id = models.PositiveIntegerField()
    host_name = models.CharField(max_length=128)
    status = models.CharField(max_length=16, default='success')
    output = models.TextField(blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']


class BuildRepository(models.Model):
    """A build repository (Git) reused for normal-mode releases."""
    name = models.CharField(max_length=128)
    url = models.CharField(max_length=512)
    credential_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
