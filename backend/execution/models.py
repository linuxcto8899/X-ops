from django.db import models
from django.conf import settings


class ExecTemplate(models.Model):
    """Parameterized command template for batch execution."""
    LANG_CHOICES = [('shell', 'Shell'), ('python', 'Python')]
    name = models.CharField(max_length=128)
    language = models.CharField(max_length=16, choices=LANG_CHOICES, default='shell')
    content = models.TextField()
    # Parameter names in {{param}} form, e.g. ["target","version"]
    params = models.JSONField(default=list, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Execution(models.Model):
    """A batch execution run across multiple hosts."""
    STATUS_CHOICES = [('running', 'Running'), ('success', 'Success'),
                      ('partial', 'Partial'), ('failed', 'Failed')]
    template = models.ForeignKey(ExecTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    language = models.CharField(max_length=16, default='shell')
    command = models.TextField()
    host_ids = models.JSONField(default=list)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='running')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Exec {self.pk}'


class ExecutionResult(models.Model):
    execution = models.ForeignKey(Execution, related_name='results', on_delete=models.CASCADE)
    host_id = models.PositiveIntegerField()
    host_name = models.CharField(max_length=128)
    exit_code = models.IntegerField(null=True, blank=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    status = models.CharField(max_length=16, default='success')
    error = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']


class ExecutionStream(models.Model):
    """Live output stream for one host in a batch execution (WebSSH-style echo).

    `output` is appended incrementally as the command runs so the frontend can
    poll and render a live terminal-like view per host.
    """
    execution = models.ForeignKey(Execution, related_name='streams', on_delete=models.CASCADE)
    host_id = models.PositiveIntegerField()
    host_name = models.CharField(max_length=128)
    output = models.TextField(blank=True, default='')
    status = models.CharField(max_length=16, default='running')  # running/success/failed
    exit_code = models.IntegerField(null=True, blank=True)
    error = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']
        unique_together = ('execution', 'host_id')

    def append(self, text):
        self.output += text
        self.save(update_fields=['output'])
