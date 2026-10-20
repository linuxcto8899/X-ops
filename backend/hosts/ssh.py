"""SSH helpers: connectivity check, command execution, host fact sync."""
import io
import paramiko
from .crypto import decrypt_value


def _client_for(host, timeout=10):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    password = decrypt_value(host.password_enc)
    private_key = decrypt_value(host.private_key_enc)
    passphrase = decrypt_value(host.key_passphrase_enc) or None
    if host.credential_id:
        cred = host.credential
        password = password or decrypt_value(cred.password_enc)
        private_key = private_key or decrypt_value(cred.private_key_enc)
        passphrase = passphrase or (decrypt_value(cred.key_passphrase_enc) or None)
    pkey = None
    if private_key:
        try:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(private_key), password=passphrase)
        except Exception:
            try:
                pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(private_key), password=passphrase)
            except Exception:
                pkey = None
    client.connect(host.hostname, port=host.port, username=host.username,
                   password=password or None, pkey=pkey, timeout=timeout,
                   banner_timeout=timeout, auth_timeout=timeout)
    return client


def check_host(host, timeout=10):
    """Return (ok, detail). Also syncs host facts when reachable."""
    try:
        client = _client_for(host, timeout=timeout)
    except Exception as exc:
        return False, f'{type(exc).__name__}: {exc}'
    try:
        facts = collect_facts(client)
        host.os_name = facts.get('os_name', '')
        host.os_version = facts.get('os_version', '')
        host.architecture = facts.get('architecture', '')
        host.cpu_count = facts.get('cpu_count')
        host.memory_mb = facts.get('memory_mb')
        host.disk_total_gb = facts.get('disk_total_gb')
        host.status = 'online'
        host.last_connected_at = __import__('django.utils.timezone', fromlist=['now']).now()
        host.save(update_fields=['os_name', 'os_version', 'architecture', 'cpu_count',
                                 'memory_mb', 'disk_total_gb', 'status', 'last_connected_at'])
        return True, 'ok'
    except Exception as exc:
        host.status = 'error'
        host.save(update_fields=['status'])
        return False, f'{type(exc).__name__}: {exc}'
    finally:
        client.close()


def collect_facts(client):
    cmd = ("echo __X_OPS__; uname -s; uname -r; uname -m; "
           "nproc; awk '/MemTotal/{print $2}' /proc/meminfo; "
           "df -P / | awk 'NR==2{print $2}'; "
           "cat /etc/os-release 2>/dev/null | grep -E '^(PRETTY_NAME|ID|VERSION_ID)='")
    _, stdout, _ = client.exec_command(cmd, timeout=15)
    lines = [l.strip() for l in stdout.read().decode('utf-8', 'replace').splitlines() if l.strip()]
    facts = {}
    if len(lines) >= 7:
        facts = {
            'os_name': lines[1], 'os_version': lines[2], 'architecture': lines[3],
            'cpu_count': int(lines[4]) if lines[4].isdigit() else None,
            'memory_mb': int(lines[5]) // 1024 if lines[5].isdigit() else None,
            'disk_total_gb': round(int(lines[6]) / 1024 / 1024, 1) if lines[6].isdigit() else None,
        }
    # Parse /etc/os-release for a friendly distro name (e.g. "Debian GNU/Linux 12 (bookworm)")
    pretty = ''
    distro_id = ''
    version_id = ''
    for ln in lines[7:]:
        if ln.startswith('PRETTY_NAME='):
            pretty = ln.split('=', 1)[1].strip('"')
        elif ln.startswith('ID='):
            distro_id = ln.split('=', 1)[1].strip('"')
        elif ln.startswith('VERSION_ID='):
            version_id = ln.split('=', 1)[1].strip('"')
    if pretty:
        # os_name = distro name, os_version = version
        facts['os_name'] = distro_id.capitalize() if distro_id else pretty.split()[0]
        facts['os_version'] = pretty
    return facts


def run_command(host, command, timeout=120):
    """Run a shell command on host, return (exit_code, stdout, stderr)."""
    client = _client_for(host, timeout=15)
    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout, get_pty=True)
        out = stdout.read().decode('utf-8', 'replace')
        err = stderr.read().decode('utf-8', 'replace')
        code = stdout.channel.recv_exit_status()
        return code, out, err
    finally:
        client.close()


def open_shell(host):
    """Open an interactive SSH shell channel for the web terminal."""
    client = _client_for(host, timeout=15)
    channel = client.invoke_shell()
    channel.settimeout(0.0)
    return client, channel
