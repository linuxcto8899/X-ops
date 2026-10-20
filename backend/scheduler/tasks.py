import subprocess
from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from hosts.models import Host
from hosts.ssh import run_command
from .models import ScheduledTask, TaskRunRecord
from .cron import next_after


@shared_task
def run_scheduled_task(task_id):
    task = ScheduledTask.objects.get(pk=task_id)
    try:
        if task.run_local or not task.host_ids:
            result = subprocess.run(task.command, shell=True, capture_output=True,
                                    text=True, timeout=600)
            output = result.stdout + result.stderr
            status = 'success' if result.returncode == 0 else 'failed'
        else:
            outputs = []
            all_ok = True
            for host in Host.objects.filter(id__in=task.host_ids):
                code, out, err = run_command(host, task.command, timeout=600)
                outputs.append(f'[{host.name}] exit={code}\n{out}{err}')
                if code != 0:
                    all_ok = False
            output = '\n'.join(outputs)
            status = 'success' if all_ok else 'failed'
        TaskRunRecord.objects.create(task=task, status=status, output=output)
    except Exception as exc:
        TaskRunRecord.objects.create(task=task, status='failed', error=f'{type(exc).__name__}: {exc}')
    task.last_run_at = timezone.now()
    task.next_run_at = compute_next_run(task)
    task.save(update_fields=['last_run_at', 'next_run_at'])
    return {'task_id': task_id}


def compute_next_run(task):
    now = timezone.now()
    if task.trigger == 'once':
        return None
    if task.trigger == 'cron' and task.cron:
        try:
            return next_after(task.cron, now)
        except ValueError:
            return None
    if task.trigger == 'interval' and task.interval:
        base = task.last_run_at or now
        return base + timedelta(seconds=task.interval)
    return None


@shared_task
def run_due_tasks():
    """Find and run all due scheduled tasks."""
    now = timezone.now()
    due = ScheduledTask.objects.filter(enabled=True, next_run_at__lte=now)
    count = 0
    for task in due:
        run_scheduled_task.delay(task.id)
        count += 1
    return {'triggered': count}
