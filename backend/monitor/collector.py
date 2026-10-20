"""Live host system-info collector over SSH: CPU, memory, network, disk, processes."""
import base64
import json
from hosts.ssh import _client_for


def _run_python(client, script):
    """Run a Python script on the remote host via base64 to preserve newlines."""
    b64 = base64.b64encode(script.encode('utf-8')).decode('ascii')
    cmd = f'python3 -c "import base64;exec(base64.b64decode(\'{b64}\').decode())"'
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', 'replace').strip()
    err = stderr.read().decode('utf-8', 'replace').strip()
    if not out:
        raise RuntimeError(f'no output: {err[:300]}')
    return out, err


def collect_metrics(host):
    """Collect a one-shot snapshot of CPU/memory/disk/network/load from a host.

    Returns a dict of metrics, or raises on failure.
    """
    script = r'''
import json, os, time
def read_cpu():
    try:
        with open('/proc/stat') as f:
            v = list(map(int, f.readline().split()[1:]))
        idle = v[3] + (v[4] if len(v) > 4 else 0)
        return idle, sum(v)
    except Exception:
        return 0, 0
def mem():
    d = {}
    with open('/proc/meminfo') as f:
        for line in f:
            k, val = line.split(':', 1)
            d[k] = int(val.strip().split()[0])
    total = d.get('MemTotal', 0)
    avail = d.get('MemAvailable', total)
    used = total - avail
    return (round(used*100/total, 1) if total else 0.0, round(used/1024, 1), round(total/1024, 1))
def disk():
    s = os.statvfs('/')
    total = s.f_blocks * s.f_frsize
    free = s.f_bavail * s.f_frsize
    used = total - free
    return (round(used*100/total, 1) if total else 0.0, round(used/1024/1024/1024, 1), round(total/1024/1024/1024, 1))
def net():
    rx = tx = 0
    try:
        with open('/proc/net/dev') as f:
            for line in f.readlines()[2:]:
                iface, values = line.split(':', 1)
                if iface.strip() == 'lo':
                    continue
                c = list(map(int, values.split()))
                rx += c[0]; tx += c[8]
    except Exception:
        pass
    return rx, tx
c1 = read_cpu()
time.sleep(1)
c2 = read_cpu()
di, dt = c2[0]-c1[0], c2[1]-c1[1]
cpu = round(max(0, min(100, (1 - di/dt)*100)), 1) if dt else 0.0
mp, mu, mt = mem()
dp, du, dtot = disk()
rx, tx = net()
load = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
print(json.dumps({'cpu_percent': cpu, 'memory_percent': mp, 'memory_used_mb': mu,
    'memory_total_mb': mt, 'disk_percent': dp, 'disk_used_gb': du, 'disk_total_gb': dtot,
    'network_rx_bytes': rx, 'network_tx_bytes': tx,
    'load_1m': round(load[0], 2), 'load_5m': round(load[1], 2), 'load_15m': round(load[2], 2)}))
'''
    client = _client_for(host, timeout=15)
    try:
        out, err = _run_python(client, script)
        return json.loads(out.splitlines()[-1])
    finally:
        client.close()


def collect_processes(host, limit=50):
    """Collect the top-N processes by CPU from a host."""
    script = r'''
import json, os
rows = []
try:
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        try:
            with open(f'/proc/{pid}/stat') as f:
                parts = f.read().split()
            comm = parts[1].strip('()')
            state = parts[2]
            utime = int(parts[13]); stime = int(parts[14])
            rss = int(parts[23])
            with open(f'/proc/{pid}/status') as f:
                status = {}
                for line in f:
                    k, _, v = line.partition(':')
                    status[k.strip()] = v.strip()
            uid = status.get('Uid', '').split('\t')[0]
            rows.append({'pid': int(pid), 'user': uid, 'cpu': utime + stime,
                         'mem_kb': rss, 'command': comm, 'state': state})
        except Exception:
            continue
except Exception:
    pass
rows.sort(key=lambda r: r['cpu'], reverse=True)
rows = rows[:%d]
for r in rows:
    r['cpu'] = 0
print(json.dumps(rows))
''' % limit
    client = _client_for(host, timeout=15)
    try:
        out, _ = _run_python(client, script)
        if not out:
            return []
        return json.loads(out.splitlines()[-1])
    finally:
        client.close()
