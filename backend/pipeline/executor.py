"""Pipeline node executor: runs each node type and handles conditional branching.

Node types:
  - param:   declare/override runtime params (no-op, just records)
  - build:   run a build command locally
  - exec:    run a shell command on target hosts
  - transfer: distribute a file/dir to hosts
  - upload:  upload a file to hosts
  - notify:  send a DingTalk/Feishu/QYWX/Push notification
"""
import json
import re
import urllib.request
from hosts.models import Host
from hosts.ssh import run_command
from files.sftp import upload_file, transfer_remote
from .models import PipelineRun


def _render(text, params):
    """Replace {{key}} placeholders with runtime params."""
    def repl(m):
        return str(params.get(m.group(1), m.group(0)))
    return re.sub(r'\{\{\s*(\w+)\s*\}\}', repl, text or '')


def run_pipeline(pipeline_run):
    """Execute a pipeline's nodes in order, honoring conditional branching."""
    pipeline = pipeline_run.pipeline
    params = dict(pipeline_run.params or {})
    nodes = pipeline.nodes or []
    node_results = []
    index = 0
    pipeline_run.status = 'running'
    pipeline_run.save(update_fields=['status'])
    while index < len(nodes):
        node = nodes[index]
        node_type = node.get('type', 'exec')
        node_name = node.get('name', f'node-{index}')
        # param node: merge declared params
        if node_type == 'param':
            declared = node.get('params', {})
            params.update({k: _render(str(v), params) for k, v in declared.items()})
            node_results.append({'node': node_name, 'type': node_type, 'status': 'success',
                                 'output': json.dumps(declared, ensure_ascii=False)})
            index += 1
            continue
        pipeline_run.current_node = node_name
        pipeline_run.node_results = node_results
        pipeline_run.params = params
        pipeline_run.save(update_fields=['current_node', 'node_results', 'params'])
        try:
            ok, output = _execute_node(node_type, node, params)
        except Exception as exc:
            ok, output = False, f'{type(exc).__name__}: {exc}'
        node_results.append({'node': node_name, 'type': node_type,
                             'status': 'success' if ok else 'failed', 'output': output})
        pipeline_run.node_results = node_results
        pipeline_run.save(update_fields=['node_results'])
        if ok:
            index = _next_index(nodes, index, 'next_on_success')
        else:
            index = _next_index(nodes, index, 'next_on_failure')
        if index is None:
            break
    pipeline_run.status = 'success' if all(r['status'] == 'success' for r in node_results) else 'failed'
    pipeline_run.node_results = node_results
    pipeline_run.save(update_fields=['status', 'node_results'])
    return pipeline_run


def _next_index(nodes, index, key):
    """Return next node index based on branch key, or None to stop."""
    node = nodes[index]
    target = node.get(key)
    if not target:
        return index + 1 if index + 1 < len(nodes) else None
    for i, n in enumerate(nodes):
        if n.get('name') == target:
            return i
    return None


def _execute_node(node_type, node, params):
    if node_type == 'build':
        return _run_build(node, params)
    if node_type == 'exec':
        return _run_exec(node, params)
    if node_type == 'transfer':
        return _run_transfer(node, params)
    if node_type == 'upload':
        return _run_upload(node, params)
    if node_type == 'notify':
        return _run_notify(node, params)
    return False, f'unknown node type: {node_type}'


def _run_build(node, params):
    cmd = _render(node.get('command', ''), params)
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    return result.returncode == 0, (result.stdout or result.stderr)


def _run_exec(node, params):
    command = _render(node.get('command', ''), params)
    host_ids = node.get('host_ids', [])
    hosts = Host.objects.filter(id__in=host_ids)
    outputs = []
    all_ok = True
    for host in hosts:
        code, out, err = run_command(host, command, timeout=node.get('timeout', 300))
        outputs.append(f'[{host.name}] exit={code}\n{out}{err}')
        if code != 0:
            all_ok = False
    return all_ok, '\n'.join(outputs)


def _run_transfer(node, params):
    host_ids = node.get('host_ids', [])
    source = _render(node.get('source', ''), params)
    target = _render(node.get('target', ''), params)
    hosts = Host.objects.filter(id__in=host_ids)
    if not hosts:
        return False, 'no hosts'
    source_host = hosts[0]
    outputs = []
    for host in hosts:
        if host.id == source_host.id:
            continue
        transfer_remote(source_host, source, target)
        outputs.append(f'[{host.name}] transferred {source} -> {target}')
    return True, '\n'.join(outputs)


def _run_upload(node, params):
    host_ids = node.get('host_ids', [])
    local_path = _render(node.get('local_path', ''), params)
    target = _render(node.get('target', ''), params)
    hosts = Host.objects.filter(id__in=host_ids)
    with open(local_path, 'rb') as f:
        data = f.read()
    outputs = []
    for host in hosts:
        upload_file(host, data, target)
        outputs.append(f'[{host.name}] uploaded to {target}')
    return True, '\n'.join(outputs)


def _run_notify(node, params):
    channel = node.get('channel', 'dingtalk')
    webhook = _render(node.get('webhook', ''), params)
    content = _render(node.get('content', ''), params)
    if not webhook:
        return False, 'webhook url required'
    if channel == 'feishu':
        payload = {'msg_type': 'text', 'content': {'text': content}}
    else:
        payload = {'msgtype': 'text', 'text': {'content': content}}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(webhook, data=data,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()
    return True, f'notified via {channel}'
