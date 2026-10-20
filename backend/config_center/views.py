from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Env, Service, AppConfig
from .serializers import EnvSerializer, ServiceSerializer, AppConfigSerializer


class EnvViewSet(viewsets.ModelViewSet):
    queryset = Env.objects.all()
    serializer_class = EnvSerializer
    search_fields = ['name']


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    search_fields = ['name']


class AppConfigViewSet(viewsets.ModelViewSet):
    queryset = AppConfig.objects.all()
    serializer_class = AppConfigSerializer
    filterset_fields = ['service', 'env']
    search_fields = ['key']


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def open_api(request, service, env):
    """Open API for applications to read config: /api/config/open/<service>/<env>/"""
    try:
        service_obj = Service.objects.get(name=service)
        env_obj = Env.objects.get(name=env)
    except (Service.DoesNotExist, Env.DoesNotExist):
        return Response({'detail': 'not found'}, status=404)
    configs = AppConfig.objects.filter(service=service_obj, env=env_obj)
    result = {}
    for cfg in configs:
        if cfg.view == 'json':
            import json
            try:
                result[cfg.key] = json.loads(cfg.value)
            except json.JSONDecodeError:
                result[cfg.key] = cfg.value
        else:
            result[cfg.key] = cfg.value
    return Response(result)
