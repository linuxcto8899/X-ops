from django.db import models


class Env(models.Model):
    """A configuration environment (e.g. dev, staging, production)."""
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    """A service (application) that holds configuration."""
    name = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AppConfig(models.Model):
    """A configuration item for a service in an environment."""
    VIEW_CHOICES = [('kv', 'KV'), ('text', 'Text'), ('json', 'JSON')]
    service = models.ForeignKey(Service, related_name='configs', on_delete=models.CASCADE)
    env = models.ForeignKey(Env, related_name='configs', on_delete=models.CASCADE)
    key = models.CharField(max_length=255)
    value = models.TextField(blank=True)
    view = models.CharField(max_length=16, choices=VIEW_CHOICES, default='kv')
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('service', 'env', 'key')
        ordering = ['key']

    def __str__(self):
        return f'{self.service.name}/{self.env.name}/{self.key}'
