from django.db import models
from django.conf import settings


class Pipeline(models.Model):
    """A node-orchestrated pipeline definition."""
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    # Ordered node definitions: [{type, name, params, next_on_success, next_on_failure}]
    nodes = models.JSONField(default=list)
    enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PipelineRun(models.Model):
    """A pipeline execution."""
    STATUS_CHOICES = [('running', 'Running'), ('success', 'Success'),
                      ('failed', 'Failed'), ('cancelled', 'Cancelled')]
    pipeline = models.ForeignKey(Pipeline, related_name='runs', on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='running')
    current_node = models.CharField(max_length=128, blank=True)
    # Per-node results: [{node, type, status, output, started_at, finished_at}]
    node_results = models.JSONField(default=list)
    # Runtime params substituted into nodes
    params = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.pipeline.name} #{self.pk}'
