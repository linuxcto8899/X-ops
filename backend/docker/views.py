from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from . import docker_ops


def _wrap(host_id, fn, *args, **kwargs):
    try:
        host = docker_ops.get_host_or_404(host_id)
    except RuntimeError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
    try:
        data = fn(host, *args, **kwargs)
        return Response(data)
    except RuntimeError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return Response({'detail': f'{type(exc).__name__}: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def info(request, host_id):
    return _wrap(host_id, docker_ops.get_info)


@api_view(['GET'])
def containers(request, host_id):
    all_c = request.query_params.get('all', '1') != '0'
    return _wrap(host_id, docker_ops.list_containers, all_c)


@api_view(['GET'])
def container_logs(request, host_id, container_id):
    lines = int(request.query_params.get('lines', 300))
    return _wrap(host_id, docker_ops.container_logs, container_id, lines)


@api_view(['POST'])
def container_action(request, host_id, container_id, action):
    return _wrap(host_id, docker_ops.container_action, container_id, action)


@api_view(['GET'])
def images(request, host_id):
    return _wrap(host_id, docker_ops.list_images)


@api_view(['POST'])
def remove_image(request, host_id, image_ref):
    return _wrap(host_id, docker_ops.remove_image, image_ref)


@api_view(['GET'])
def networks(request, host_id):
    return _wrap(host_id, docker_ops.list_networks)