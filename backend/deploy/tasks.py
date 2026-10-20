"""Deploy execution logic: build, release, rollback."""
import os
import shutil
import tempfile
from celery import shared_task
from hosts.models import Host
from hosts.ssh import run_command
from files.sftp import upload_file
from .models import Release, ReleaseResult


@shared_task
def execute_release(release_id):
    """Build (if normal mode) then release to target hosts."""
    release = Release.objects.select_related('app').get(pk=release_id)
    app = release.app
    release.status = 'releasing'
    release.save(update_fields=['status'])
    hosts = Host.objects.filter(id__in=app.host_ids)
    results = []
    for host in hosts:
        try:
            if app.mode == 'custom':
                code, out, err = run_command(host, app.deploy_script, timeout=600)
                status_ = 'success' if code == 0 else 'failed'
                results.append(ReleaseResult.objects.create(
                    release=release, host_id=host.id, host_name=host.name,
                    status=status_, output=out, error=err))
            else:
                # Normal mode: build artifacts are uploaded to target_path
                build_dir = _build_artifacts(release)
                _upload_dir(host, build_dir, app.target_path)
                results.append(ReleaseResult.objects.create(
                    release=release, host_id=host.id, host_name=host.name, status='success'))
                shutil.rmtree(build_dir, ignore_errors=True)
        except Exception as exc:
            results.append(ReleaseResult.objects.create(
                release=release, host_id=host.id, host_name=host.name,
                status='failed', error=f'{type(exc).__name__}: {exc}'))
    ok = sum(1 for r in results if r.status == 'success')
    total = len(results)
    release.status = 'success' if total and ok == total else 'failed'
    release.save(update_fields=['status'])
    return {'release_id': release_id, 'status': release.status, 'total': total, 'ok': ok}


def _build_artifacts(release):
    """Clone repo, run build command, return dir of artifacts."""
    app = release.app
    tmp = tempfile.mkdtemp(prefix='xops-build-')
    repo_dir = os.path.join(tmp, 'repo')
    run_command_local = _local_run
    run_command_local(f'git clone -b {app.repo_branch} --depth 1 {app.repo_url} {repo_dir}')
    if app.build_command:
        run_command_local(f'cd {repo_dir} && {app.build_command}')
    return repo_dir


def _local_run(cmd):
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def _upload_dir(host, local_dir, remote_dir):
    client = None
    from hosts.ssh import _client_for
    client = _client_for(host, timeout=15)
    sftp = client.open_sftp()
    try:
        try:
            sftp.mkdir(remote_dir)
        except IOError:
            pass
        for root, dirs, files in os.walk(local_dir):
            rel = os.path.relpath(root, local_dir)
            target = remote_dir if rel == '.' else os.path.join(remote_dir, rel).replace('\\', '/')
            try:
                sftp.mkdir(target)
            except IOError:
                pass
            for f in files:
                local = os.path.join(root, f)
                remote = os.path.join(target, f).replace('\\', '/')
                with open(local, 'rb') as lf:
                    with sftp.open(remote, 'wb') as rf:
                        rf.write(lf.read())
    finally:
        sftp.close()
        client.close()


@shared_task
def rollback_release(release_id):
    """Mark a release as rolled back (manual intervention placeholder)."""
    release = Release.objects.get(pk=release_id)
    release.status = 'rolled_back'
    release.save(update_fields=['status'])
    return {'release_id': release_id, 'status': 'rolled_back'}
