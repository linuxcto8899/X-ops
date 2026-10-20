"""Symmetric encryption for sensitive values (passwords, private keys).

Uses Fernet with a key derived from DJANGO_SECRET_KEY. In production, set a
strong DJANGO_SECRET_KEY; the encryption key is derived from it.
"""
import base64
import hashlib
from django.conf import settings
from cryptography.fernet import Fernet


def _fernet():
    digest = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_value(value):
    return _fernet().encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_value(value):
    if not value:
        return ''
    return _fernet().decrypt(value.encode('utf-8')).decode('utf-8')
