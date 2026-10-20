from django.db import models
from django.conf import settings


class ScheduledTask(models.Model):
    """A task triggered once, on cron, on fixed interval, or by monitor alert."""
    TRIGGER_CHOICES = [('once', 'Once'), ('cron', 'Cron'), ('interval', 'Interval'),
                       ('monitor', 'Monitor Alert')]
    name = models.CharField(max_length=128)
    trigger = models.CharField(max_length=16, choices=TRIGGER_CHOICES, default='cron')
    # cron expression (for trigger=cron), e.g. "0 3 * * *"
    cron = models.CharField(max_length=100, blank=True)
    # interval seconds (for trigger=interval)
    interval = models.PositiveIntegerField(null=True, blank=True)
    # run_at (for trigger=once)
    run_at = models.DateTimeField(null=True, blank=True)
    # monitor rule id (for trigger=monitor)
    monitor_rule_id = models.PositiveIntegerField(null=True, blank=True)
    # Command to execute (on hosts or locally)
    command = models.TextField()
    # Empty = run locally; otherwise target hosts
    host_ids = models.JSONField(default=list)
    run_local = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['enabled', 'next_run_at'])]

    def __str__(self):
        return self.name


class TaskRunRecord(models.Model):
    task = models.ForeignKey(ScheduledTask, related_name='runs', on_delete=models.CASCADE)
    status = models.CharField(max_length=16, default='success')
    output = models.TextField(blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
