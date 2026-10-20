"""Alert delivery via NotifyChannel configs (SMTP / DingTalk / QYWX / Feishu / Server酱).

A contact's channels map may reference a NotifyChannel by id (int) or hold a
recipient address / raw webhook URL directly (back-compat).
"""
import json
import logging
import urllib.parse
import urllib.request
from celery import shared_task
from django.core.mail import EmailMessage, get_connection
from .models import AlertGroup, NotifyChannel

logger = logging.getLogger(__name__)


@shared_task
def notify_alert(group_id, title, content):
    try:
        group = AlertGroup.objects.get(pk=group_id)
    except AlertGroup.DoesNotExist:
        return {'error': 'group not found'}
    delivered = []
    failed = []
    for contact in group.contacts.all():
        channels = contact.channels or {}
        for kind, value in channels.items():
            if value in (None, ''):
                continue
            try:
                _deliver(kind, value, title, content)
                delivered.append(f'{kind}:{value}')
            except Exception as exc:
                logger.warning('alert %s failed: %s', kind, exc)
                failed.append(f'{kind}:{exc}')
    return {'delivered': delivered, 'failed': failed}


def _resolve_target(kind, value):
    """If value is an int, look up a NotifyChannel and return its config."""
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        ch = NotifyChannel.objects.filter(pk=int(value), enabled=True).first()
        if not ch:
            raise RuntimeError('notify channel not found or disabled')
        return ch
    return None


def _deliver(kind, value, title, content):
    channel = _resolve_target(kind, value)
    if channel:
        kind = channel.kind
        cfg = channel.config or {}
    else:
        cfg = {}

    if kind == 'email' or kind == 'smtp':
        _send_email(cfg, value if isinstance(value, str) else cfg.get('from_email'), title, content)
    elif kind == 'dingtalk':
        url = cfg.get('webhook_url') if channel else value
        _post_webhook(url, {'msgtype': 'text', 'text': {'content': f'{title}\n{content}'}})
    elif kind == 'qywx':
        url = cfg.get('webhook_url') if channel else value
        _post_webhook(url, {'msgtype': 'text', 'text': {'content': f'{title}\n{content}'}})
    elif kind == 'feishu':
        url = cfg.get('webhook_url') if channel else value
        _post_webhook(url, {'msg_type': 'text', 'content': {'text': f'{title}\n{content}'}})
    elif kind == 'serverchan':
        key = cfg.get('send_key') if channel else value
        _send_serverchan(key, title, content)
    elif kind == 'wechat':
        # Back-compat: generic wechat webhook behaves like a text webhook
        _post_webhook(value, {'msgtype': 'text', 'text': {'content': f'{title}\n{content}'}})
    else:
        raise RuntimeError(f'unsupported channel kind: {kind}')


def _send_email(cfg, to_addr, title, content):
    """Send email using per-channel SMTP config; fall back to global settings."""
    host = cfg.get('host') or ''
    if host:
        conn = get_connection(
            host=host,
            port=int(cfg.get('port') or 25),
            username=cfg.get('username') or '',
            password=cfg.get('password') or '',
            use_tls=bool(cfg.get('use_tls', False)),
            use_ssl=bool(cfg.get('use_ssl', False)),
            fail_silently=False,
        )
        msg = EmailMessage(title, content, cfg.get('from_email') or cfg.get('username') or 'ops@localhost',
                           [to_addr], connection=conn)
        msg.send()
    else:
        from django.conf import settings
        EmailMessage(title, content, settings.DEFAULT_FROM_EMAIL or 'ops@localhost',
                     [to_addr]).send()


def _send_serverchan(send_key, title, content):
    url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = urllib.parse.urlencode({'title': title, 'desp': content}).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def _post_webhook(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def test_channel(channel, title, content, target=None):
    """Send a test message through a NotifyChannel to an optional target.

    target semantics:
      - smtp: recipient email address (required)
      - dingtalk/qywx/feishu: ignored (webhook is the target)
      - serverchan: ignored (send key is the target)
    """
    cfg = channel.config or {}
    kind = channel.kind
    if kind == 'smtp':
        if not target:
            raise RuntimeError('SMTP 测试需要填写收件邮箱')
        _send_email(cfg, target, title, content)
        return {'ok': True, 'detail': f'邮件已发送至 {target}'}
    elif kind in ('dingtalk', 'qywx', 'feishu'):
        url = cfg.get('webhook_url')
        if not url:
            raise RuntimeError('未配置 webhook_url')
        if kind == 'dingtalk':
            _post_webhook(url, {'msgtype': 'text', 'text': {'content': f'{title}\n{content}'}})
        elif kind == 'qywx':
            _post_webhook(url, {'msgtype': 'text', 'text': {'content': f'{title}\n{content}'}})
        else:
            _post_webhook(url, {'msg_type': 'text', 'content': {'text': f'{title}\n{content}'}})
        return {'ok': True, 'detail': f'{channel.name} 测试消息已发送'}
    elif kind == 'serverchan':
        key = cfg.get('send_key')
        if not key:
            raise RuntimeError('未配置 send_key')
        _send_serverchan(key, title, content)
        return {'ok': True, 'detail': 'Server酱 测试消息已发送'}
    return {'ok': False, 'detail': f'未知渠道类型: {kind}'}