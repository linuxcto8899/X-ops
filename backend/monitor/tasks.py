from celery import shared_task
from hosts.models import Host
from .models import HostMetric, HostProcess, MonitorRule, MonitorRecord, AlertRecord
from .collector import collect_metrics, collect_processes
from .alerts import notify_alert


@shared_task
def collect_host_metrics(host_id):
    try:
        host = Host.objects.get(pk=host_id)
    except Host.DoesNotExist:
        return {'error': 'host not found'}
    try:
        metrics = collect_metrics(host)
    except Exception as exc:
        return {'host_id': host_id, 'error': f'{type(exc).__name__}: {exc}'}
    HostMetric.objects.create(host_id=host.id, host_name=host.name, **metrics)
    return {'host_id': host_id, 'ok': True}


@shared_task
def collect_all_host_metrics():
    hosts = Host.objects.all()
    for host in hosts:
        collect_host_metrics.delay(host.id)
    return {'hosts': hosts.count()}


@shared_task
def collect_host_processes(host_id):
    try:
        host = Host.objects.get(pk=host_id)
    except Host.DoesNotExist:
        return {'error': 'host not found'}
    try:
        processes = collect_processes(host)
    except Exception as exc:
        return {'host_id': host_id, 'error': f'{type(exc).__name__}: {exc}'}
    HostProcess.objects.create(host_id=host.id, host_name=host.name, processes=processes)
    return {'host_id': host_id, 'processes': len(processes)}


@shared_task
def evaluate_monitor_rules():
    """Run all enabled monitor rules and fire alerts."""
    fired = 0
    for rule in MonitorRule.objects.filter(enabled=True):
        ok, detail = _check_rule(rule)
        MonitorRecord.objects.create(rule=rule, ok=ok, detail=detail)
        if not ok:
            AlertRecord.objects.create(
                rule=rule, title=f'[{rule.get_type_display()}] {rule.name}',
                content=detail, level='warning', status='firing')
            if rule.notify_group_id:
                notify_alert.delay(rule.notify_group_id, rule.name, detail)
            fired += 1
    return {'fired': fired}


def _check_rule(rule):
    """Return (ok, detail) for a monitor rule."""
    from hosts.ssh import run_command
    try:
        if rule.type == 'ping':
            code, out, err = run_command(rule.host, f'ping -c 3 -W 2 {rule.target}', timeout=30) if rule.host else (1, '', 'no host')
            return (code == 0), out or err
        if rule.type == 'port':
            cmd = f'bash -c "</dev/tcp/{rule.target}/{rule.port}" && echo open || echo closed'
            code, out, err = run_command(rule.host, cmd, timeout=20) if rule.host else (1, '', 'no host')
            return (out.strip() == 'open'), out or err
        if rule.type == 'process':
            code, out, err = run_command(rule.host, f'pgrep -f {rule.target} >/dev/null && echo running || echo stopped', timeout=20) if rule.host else (1, '', 'no host')
            return (out.strip() == 'running'), out or err
        if rule.type == 'site':
            code, out, err = run_command(rule.host, f'curl -s -o /dev/null -w "%{{http_code}}" -m 10 {rule.target}', timeout=20) if rule.host else (1, '', 'no host')
            return (out.strip().startswith('2') or out.strip().startswith('3')), f'HTTP {out.strip()}'
        if rule.type == 'script':
            code, out, err = run_command(rule.host, rule.target, timeout=60) if rule.host else (1, '', 'no host')
            return (code == 0), out or err
        return True, 'unknown type'
    except Exception as exc:
        return False, f'{type(exc).__name__}: {exc}'
