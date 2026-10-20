import time
from datetime import timezone as dt_timezone
from celery import shared_task
from django.utils import timezone
from hosts.models import Host
from hosts.ssh import _client_for
from .models import Execution, ExecutionResult, ExecutionStream


@shared_task
def run_batch_execution(execution_id):
    """Run a command on each host, streaming output live into ExecutionStream.

    Each host gets its own ExecutionStream row that is appended to in real time,
    so the frontend can render a WebSSH-style live echo per host.
    """
    execution = Execution.objects.get(pk=execution_id)
    hosts = Host.objects.filter(id__in=execution.host_ids)
    results = []
    for host in hosts:
        start = time.time()
        stream, _ = ExecutionStream.objects.get_or_create(
            execution=execution, host_id=host.id,
            defaults={'host_name': host.name})
        try:
            exit_code, output, error = _stream_command(host, execution.command, stream)
            stream.status = 'success' if exit_code == 0 else 'failed'
            stream.exit_code = exit_code
            stream.error = error
            stream.finished_at = timezone.now()
            stream.save(update_fields=['status', 'exit_code', 'error', 'finished_at'])
            results.append(ExecutionResult.objects.create(
                execution=execution, host_id=host.id, host_name=host.name,
                exit_code=exit_code, stdout=output, stderr=error,
                status='success' if exit_code == 0 else 'failed',
                duration_ms=int((time.time() - start) * 1000)))
        except Exception as exc:
            msg = f'{type(exc).__name__}: {exc}'
            stream.status = 'failed'
            stream.error = msg
            stream.finished_at = timezone.now()
            stream.save(update_fields=['status', 'error', 'finished_at'])
            results.append(ExecutionResult.objects.create(
                execution=execution, host_id=host.id, host_name=host.name,
                status='failed', error=msg,
                duration_ms=int((time.time() - start) * 1000)))
    ok = sum(1 for r in results if r.status == 'success')
    total = len(results)
    if total == 0:
        execution.status = 'failed'
    elif ok == total:
        execution.status = 'success'
    elif ok == 0:
        execution.status = 'failed'
    else:
        execution.status = 'partial'
    execution.save(update_fields=['status'])
    return {'execution_id': execution_id, 'status': execution.status, 'total': total, 'ok': ok}


def _stream_command(host, command, stream):
    """Run a command on a host, streaming stdout/stderr line-by-line into the stream.

    Returns (exit_code, full_stdout, full_stderr).
    """
    client = _client_for(host, timeout=15)
    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=600, get_pty=True)
        full_out = []
        full_err = []
        # Read stdout and stderr incrementally
        import select
        channels = [stdout.channel, stderr.channel]
        while True:
            r, _, _ = select.select(channels, [], [], 0.5)
            if not r:
                # check if both channels are done
                if stdout.channel.exit_status_ready() and stderr.channel.exit_status_ready():
                    # drain remaining
                    _drain(stdout, full_out, stream)
                    _drain(stderr, full_err, stream)
                    break
                continue
            for ch in r:
                if ch is stdout.channel:
                    _drain(stdout, full_out, stream)
                elif ch is stderr.channel:
                    _drain(stderr, full_err, stream)
            if stdout.channel.exit_status_ready() and stderr.channel.exit_status_ready():
                _drain(stdout, full_out, stream)
                _drain(stderr, full_err, stream)
                break
        code = stdout.channel.recv_exit_status()
        return code, ''.join(full_out), ''.join(full_err)
    finally:
        client.close()


def _drain(channel_obj, collector, stream):
    """Read all currently available data from a channel and append to stream."""
    try:
        while True:
            chunk = channel_obj.channel.recv(8192)
            if not chunk:
                break
            text = chunk.decode('utf-8', 'replace')
            collector.append(text)
            stream.append(text)
    except Exception:
        pass