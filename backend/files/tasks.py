import os
from celery import shared_task
from django.conf import settings
from hosts.models import Host
from .models import FileTransfer, FileTransferResult, UploadedFile
from .sftp import upload_file, transfer_remote


@shared_task
def run_file_transfer(transfer_id):
    transfer = FileTransfer.objects.get(pk=transfer_id)
    hosts = Host.objects.filter(id__in=transfer.host_ids)
    results = []
    for host in hosts:
        try:
            if transfer.kind == 'upload':
                uf = transfer.uploaded_file
                local_path = os.path.join(settings.MEDIA_ROOT, uf.path)
                with open(local_path, 'rb') as f:
                    data = f.read()
                upload_file(host, data, transfer.target_path)
            else:
                # remote: source_path is on the first host, distribute to the rest
                source_host = hosts[0]
                if host.id == source_host.id:
                    # same host, no-op
                    results.append(FileTransferResult.objects.create(
                        transfer=transfer, host_id=host.id, host_name=host.name, status='success'))
                    continue
                transfer_remote(source_host, transfer.source_path, transfer.target_path)
            results.append(FileTransferResult.objects.create(
                transfer=transfer, host_id=host.id, host_name=host.name, status='success'))
        except Exception as exc:
            results.append(FileTransferResult.objects.create(
                transfer=transfer, host_id=host.id, host_name=host.name,
                status='failed', error=f'{type(exc).__name__}: {exc}'))
    ok = sum(1 for r in results if r.status == 'success')
    total = len(results)
    if total == 0:
        transfer.status = 'failed'
    elif ok == total:
        transfer.status = 'success'
    elif ok == 0:
        transfer.status = 'failed'
    else:
        transfer.status = 'partial'
    transfer.save(update_fields=['status'])
    return {'transfer_id': transfer_id, 'status': transfer.status, 'total': total, 'ok': ok}
