from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    """A named role bundling fine-grained permissions."""
    name = models.CharField(max_length=64, unique=True)
    # JSON list of permission keys, e.g. ["host.view", "exec.run", "deploy.release"]
    perms = models.JSONField(default=list, blank=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [('admin', 'Administrator'), ('user', 'User')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    roles = models.ManyToManyField(Role, blank=True, related_name='users')
    phone = models.CharField(max_length=32, blank=True)
    wechat = models.CharField(max_length=64, blank=True)
    dingtalk = models.CharField(max_length=64, blank=True)
    feishu = models.CharField(max_length=64, blank=True)
    # MFA secret (TOTP). Empty = MFA disabled.
    mfa_secret = models.CharField(max_length=64, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    is_ldap = models.BooleanField(default=False)

    def has_permission(self, perm):
        if self.is_superuser or self.role == 'admin':
            return True
        for r in self.roles.all():
            if perm in (r.perms or []):
                return True
        return False
