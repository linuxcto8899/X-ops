"""SFTP helpers for file management and distribution."""
import io
import posixpath
from hosts.models import Host
from hosts.crypto import decrypt_value
from hosts.ssh import _client_for


def _sftp(host):
    client = _client_for(host, timeout=15)
    sftp = client.open_sftp()
    return client, sftp


def list_dir(host, path='.'):
    client, sftp = _sftp(host)
    try:
        items = []
        for entry in sftp.listdir_attr(path):
            items.append({
                'name': entry.filename,
                'is_dir': entry.st_mode is not None and (entry.st_mode & 0o040000) != 0,
                'size': entry.st_size,
                'mtime': entry.st_mtime,
            })
        return items
    finally:
        sftp.close()
        client.close()


def read_file(host, path):
    client, sftp = _sftp(host)
    try:
        with sftp.open(path, 'rb') as f:
            return f.read()
    finally:
        sftp.close()
        client.close()


def write_file(host, path, data):
    client, sftp = _sftp(host)
    try:
        with sftp.open(path, 'wb') as f:
            f.write(data)
        return True
    finally:
        sftp.close()
        client.close()


def delete_path(host, path):
    client, sftp = _sftp(host)
    try:
        try:
            sftp.remove(path)
        except IOError:
            sftp.rmdir(path)
        return True
    finally:
        sftp.close()
        client.close()


def upload_file(host, local_bytes, remote_path):
    client, sftp = _sftp(host)
    try:
        with sftp.open(remote_path, 'wb') as f:
            f.write(local_bytes)
        return True
    finally:
        sftp.close()
        client.close()


def download_file(host, remote_path):
    return read_file(host, remote_path)


def transfer_remote(host, source_path, target_path):
    """Copy a remote directory/file from one host to another host."""
    client, sftp = _sftp(host)
    try:
        stat = sftp.stat(source_path)
        if stat.st_mode & 0o040000:
            # directory: walk and copy recursively
            _copy_dir(sftp, source_path, target_path)
        else:
            with sftp.open(source_path, 'rb') as src:
                data = src.read()
            with sftp.open(target_path, 'wb') as dst:
                dst.write(data)
        return True
    finally:
        sftp.close()
        client.close()


def _copy_dir(sftp, source, target):
    try:
        sftp.mkdir(target)
    except IOError:
        pass
    for entry in sftp.listdir_attr(source):
        s = posixpath.join(source, entry.filename)
        t = posixpath.join(target, entry.filename)
        if entry.st_mode & 0o040000:
            _copy_dir(sftp, s, t)
        else:
            with sftp.open(s, 'rb') as src:
                with sftp.open(t, 'wb') as dst:
                    dst.write(src.read())
