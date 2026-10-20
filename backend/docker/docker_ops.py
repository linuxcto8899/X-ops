"""Docker management over SSH: containers, images, networks, logs, operations."""
import json
from hosts.models import Host
from hosts.ssh import run_command

CONTAINER_FMT = '{{json .}}'
IMAGE_FMT = '{{json .}}'
NETWORK_FMT = '{{json .}}'


def _parse_json_lines(out):
    """Parse each line of docker --format '{{json .}}' output."""
    items = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except (ValueError, json.JSONDecodeError):
            # single-key outputs like {{.ID}} are bare strings
            items.append({'raw': line})
    return items


def _run(host, cmd, timeout=60):
    code, out, err = run_command(host, cmd, timeout=timeout)
    return code, out.strip(), err.strip()


def docker_available(host):
    code, out, err = _run(host, 'docker version --format "{{.Server.Version}}"', timeout=20)
    return code == 0, out, err


def get_info(host):
    """Docker overview: version, containers/images/volumes/networks counts, server info."""
    ok, ver, err = docker_available(host)
    if not ok:
        return {'ok': False, 'detail': err or 'docker not available'}
    info = {'ok': True, 'version': ver}
    # container counts by state
    code, out, _ = _run(host, "docker ps -a --format '{{.State}}' | sort | uniq -c | awk '{printf \"%s=%s\\n\", $2, $1}'")
    counts = {}
    if code == 0:
        for ln in out.splitlines():
            k, _, v = ln.partition('=')
            if k:
                counts[k] = int(v or 0)
    info['containers'] = counts
    # images / networks / volumes counts
    for name, cmd in [
        ('images', "docker images -q | wc -l"),
        ('networks', "docker network ls -q | wc -l"),
        ('volumes', "docker volume ls -q | wc -l"),
    ]:
        code, out, _ = _run(host, cmd)
        info[name] = int(out.split()[-1]) if code == 0 and out else 0
    # engine info lines
    code, out, _ = _run(host, "docker info --format 'OS={{.OperatingSystem}}|ARCH={{.Architecture}}|CPU={{.NCPU}}|MEM={{.MemTotal}}|IMG={{.Images}}|CT={{.Containers}}|RUN={{.ContainersRunning}}'")
    if code == 0:
        kv = {}
        for part in out.split('|'):
            k, _, v = part.partition('=')
            if k:
                kv[k] = v
        info['engine'] = kv
    return info


def list_containers(host, all_containers=True):
    flag = '-a' if all_containers else ''
    code, out, err = _run(host, f"docker ps {flag} --no-trunc --format '{CONTAINER_FMT}'")
    if code != 0:
        raise RuntimeError(err or 'docker ps failed')
    return _parse_json_lines(out)


def container_logs(host, container_id, lines=300):
    code, out, err = _run(host, f"docker logs --tail {lines} {container_id}", timeout=30)
    if code != 0 and 'Error' in err and 'No such container' in err:
        raise RuntimeError('container not found')
    return out or (err if 'Error' not in err else err)


def container_action(host, container_id, action):
    """start / stop / restart / pause / unpause / remove"""
    cmd = {
        'start': f'docker start {container_id}',
        'stop': f'docker stop {container_id}',
        'restart': f'docker restart {container_id}',
        'pause': f'docker pause {container_id}',
        'unpause': f'docker unpause {container_id}',
        'remove': f'docker rm -f {container_id}',
    }.get(action)
    if not cmd:
        raise RuntimeError(f'unsupported action: {action}')
    code, out, err = _run(host, cmd, timeout=60)
    if code != 0:
        raise RuntimeError(err or f'{action} failed')
    return {'ok': True, 'detail': out or f'{action} ok'}


def list_images(host):
    code, out, err = _run(host, f"docker images --format '{IMAGE_FMT}'")
    if code != 0:
        raise RuntimeError(err or 'docker images failed')
    return _parse_json_lines(out)


def remove_image(host, image_ref):
    code, out, err = _run(host, f'docker rmi {image_ref}', timeout=60)
    if code != 0:
        raise RuntimeError(err or 'docker rmi failed')
    return {'ok': True, 'detail': out or 'image removed'}


def list_networks(host):
    code, out, err = _run(host, f"docker network ls --format '{NETWORK_FMT}'")
    if code != 0:
        raise RuntimeError(err or 'docker network ls failed')
    return _parse_json_lines(out)


def get_host_or_404(host_id):
    try:
        return Host.objects.get(pk=host_id)
    except Host.DoesNotExist:
        raise RuntimeError('host not found')