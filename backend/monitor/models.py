from django.db import models
from django.conf import settings


class HostMetric(models.Model):
    """A periodic snapshot of a host's live system metrics."""
    host_id = models.PositiveIntegerField()
    host_name = models.CharField(max_length=128)
    cpu_percent = models.FloatField(default=0)
    memory_percent = models.FloatField(default=0)
    memory_used_mb = models.FloatField(default=0)
    memory_total_mb = models.FloatField(default=0)
    disk_percent = models.FloatField(default=0)
    disk_used_gb = models.FloatField(default=0)
    disk_total_gb = models.FloatField(default=0)
    network_rx_bytes = models.BigIntegerField(default=0)
    network_tx_bytes = models.BigIntegerField(default=0)
    load_1m = models.FloatField(default=0)
    load_5m = models.FloatField(default=0)
    load_15m = models.FloatField(default=0)
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-captured_at']
        indexes = [models.Index(fields=['host_id', '-captured_at'])]


class HostProcess(models.Model):
    """A snapshot of running processes on a host."""
    host_id = models.PositiveIntegerField()
    host_name = models.CharField(max_length=128)
    processes = models.JSONField(default=list)  # [{pid,user,cpu,mem,command}]
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-captured_at']


class MonitorRule(models.Model):
    """A monitor check: site/port/ping/process/script."""
    TYPE_CHOICES = [('site', 'Site'), ('port', 'Port'), ('ping', 'Ping'),
                    ('process', 'Process'), ('script', 'Script')]
    name = models.CharField(max_length=128)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    # For site/port/ping: target. For process: process name. For script: command.
    target = models.CharField(max_length=512)
    port = models.PositiveIntegerField(null=True, blank=True)
    host = models.ForeignKey('hosts.Host', null=True, blank=True, on_delete=models.SET_NULL)
    interval = models.PositiveIntegerField(default=60)
    enabled = models.BooleanField(default=True)
    # Alert linkage: notify group / trigger scheduled task
    notify_group_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MonitorRecord(models.Model):
    rule = models.ForeignKey(MonitorRule, related_name='records', on_delete=models.CASCADE)
    ok = models.BooleanField(default=True)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class NotifyChannel(models.Model):
    """Global outbound notification channel config (SMTP / bot webhooks / Server酱).

    config keys by kind:
      - smtp:       {host, port, username, password, from_email, use_tls}
      - dingtalk:   {webhook_url}
      - qywx:       {webhook_url}
      - feishu:     {webhook_url}
      - serverchan: {send_key}
    """
    KIND_CHOICES = [
        ('smtp', 'SMTP 邮件'),
        ('dingtalk', '钉钉机器人'),
        ('qywx', '企业微信机器人'),
        ('feishu', '飞书机器人'),
        ('serverchan', 'Server酱'),
    ]
    name = models.CharField(max_length=64)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    config = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class AlertContact(models.Model):
    name = models.CharField(max_length=64)
    # JSON: {"email":"user@example.com", "dingtalk":3, "qywx":2, "feishu":4, "serverchan":5}
    # Value may be a recipient address (email), a raw webhook URL (back-compat),
    # or a NotifyChannel id (int) referencing a global channel config.
    channels = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AlertGroup(models.Model):
    name = models.CharField(max_length=64)
    contacts = models.ManyToManyField(AlertContact, blank=True, related_name='groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AlertRecord(models.Model):
    rule = models.ForeignKey(MonitorRule, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    level = models.CharField(max_length=16, default='warning')  # info/warning/critical
    status = models.CharField(max_length=16, default='firing')  # firing/resolved
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
