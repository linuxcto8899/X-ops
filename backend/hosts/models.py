from django.db import models
from django.conf import settings
from .crypto import encrypt_value


class HostGroup(models.Model):
    name = models.CharField(max_length=64, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Credential(models.Model):
    """Centralized password / private-key store reused across hosts and builds."""
    name = models.CharField(max_length=64)
    username = models.CharField(max_length=128)
    # Encrypted. Either password or private_key (or both).
    password_enc = models.TextField(blank=True)
    private_key_enc = models.TextField(blank=True)
    key_passphrase_enc = models.TextField(blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def set_password(self, value):
        self.password_enc = encrypt_value(value) if value else ''

    def set_private_key(self, value):
        self.private_key_enc = encrypt_value(value) if value else ''

    def set_key_passphrase(self, value):
        self.key_passphrase_enc = encrypt_value(value) if value else ''


class Host(models.Model):
    name = models.CharField(max_length=128)
    hostname = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=22)
    username = models.CharField(max_length=128)
    # Encrypted inline credentials (or reference a Credential).
    password_enc = models.TextField(blank=True)
    private_key_enc = models.TextField(blank=True)
    key_passphrase_enc = models.TextField(blank=True)
    credential = models.ForeignKey(Credential, null=True, blank=True, on_delete=models.SET_NULL)
    groups = models.ManyToManyField(HostGroup, blank=True, related_name='hosts')
    # Synced host facts
    os_name = models.CharField(max_length=255, blank=True)
    os_version = models.CharField(max_length=120, blank=True)
    architecture = models.CharField(max_length=80, blank=True)
    cpu_count = models.PositiveIntegerField(null=True, blank=True)
    memory_mb = models.PositiveIntegerField(null=True, blank=True)
    disk_total_gb = models.FloatField(null=True, blank=True)
    # Connectivity status
    status = models.CharField(max_length=20, default='unknown')  # unknown/online/offline/error
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_connected_at = models.DateTimeField(null=True, blank=True)
    # Cloud provider / region / expiry
    cloud_provider = models.CharField(max_length=64, blank=True, default='')  # aliyun/tencent/aws/azure/gcp/other
    region = models.CharField(max_length=64, blank=True, default='')  # e.g. cn-hangzhou / us-east-1
    region_code = models.CharField(max_length=8, blank=True, default='')  # ISO country code for flag
    expire_at = models.DateTimeField(null=True, blank=True)  # host expiry time
    remark = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.hostname})'

    def set_password(self, value):
        self.password_enc = encrypt_value(value) if value else ''

    def set_private_key(self, value):
        self.private_key_enc = encrypt_value(value) if value else ''

    def set_key_passphrase(self, value):
        self.key_passphrase_enc = encrypt_value(value) if value else ''
