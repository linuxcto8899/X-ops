from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from hosts.models import Host
from .models import (HostMetric, HostProcess, MonitorRule, MonitorRecord,
                     AlertContact, AlertGroup, AlertRecord, NotifyChannel)
from .serializers import (HostMetricSerializer, HostProcessSerializer, MonitorRuleSerializer,
                          MonitorRecordSerializer, AlertContactSerializer,
                          AlertGroupSerializer, AlertRecordSerializer, NotifyChannelSerializer)
from .collector import collect_metrics, collect_processes
from .tasks import collect_host_metrics, collect_host_processes


class HostMetricViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HostMetric.objects.all()
    serializer_class = HostMetricSerializer
    filterset_fields = ['host_id']


class HostProcessViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HostProcess.objects.all()
    serializer_class = HostProcessSerializer
    filterset_fields = ['host_id']


class MonitorRuleViewSet(viewsets.ModelViewSet):
    queryset = MonitorRule.objects.all()
    serializer_class = MonitorRuleSerializer
    search_fields = ['name']
    filterset_fields = ['type', 'enabled']

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        rule = self.get_object()
        from .tasks import _check_rule
        ok, detail = _check_rule(rule)
        MonitorRecord.objects.create(rule=rule, ok=ok, detail=detail)
        return Response({'ok': ok, 'detail': detail})


class MonitorRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonitorRecord.objects.all()
    serializer_class = MonitorRecordSerializer
    filterset_fields = ['rule', 'ok']


class AlertContactViewSet(viewsets.ModelViewSet):
    queryset = AlertContact.objects.all()
    serializer_class = AlertContactSerializer
    search_fields = ['name']


class AlertGroupViewSet(viewsets.ModelViewSet):
    queryset = AlertGroup.objects.all()
    serializer_class = AlertGroupSerializer
    search_fields = ['name']


class AlertRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AlertRecord.objects.all()
    serializer_class = AlertRecordSerializer
    filterset_fields = ['status', 'level']


class NotifyChannelViewSet(viewsets.ModelViewSet):
    queryset = NotifyChannel.objects.all()
    serializer_class = NotifyChannelSerializer
    search_fields = ['name']
    filterset_fields = ['kind', 'enabled']

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Send a test notification through the channel."""
        channel = self.get_object()
        title = request.data.get('title', 'X-ops 测试通知')
        content = request.data.get('content', '这是一条来自 X-ops 报警中心的测试消息。')
        target = request.data.get('target', '')
        try:
            from .alerts import test_channel
            result = test_channel(channel, title, content, target)
            return Response(result)
        except Exception as exc:
            return Response({'ok': False, 'detail': f'{type(exc).__name__}: {exc}'},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def host_live_metrics(request, host_id):
    """Return a live snapshot of a host's CPU/memory/network/disk (on-demand)."""
    try:
        host = Host.objects.get(pk=host_id)
    except Host.DoesNotExist:
        return Response({'detail': 'host not found'}, status=status.HTTP_404_NOT_FOUND)
    try:
        metrics = collect_metrics(host)
        HostMetric.objects.create(host_id=host.id, host_name=host.name, **metrics)
        return Response(metrics)
    except Exception as exc:
        return Response({'detail': f'{type(exc).__name__}: {exc}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def host_metric_history(request, host_id):
    """Return metric history for charting. ?limit=N&field=cpu_percent"""
    limit = int(request.query_params.get('limit', 100))
    field = request.query_params.get('field')
    qs = HostMetric.objects.filter(host_id=host_id).order_by('-captured_at')[:limit]
    rows = list(reversed(list(qs)))
    data = [{
        'time': m.captured_at.strftime('%H:%M:%S'),
        'cpu_percent': m.cpu_percent, 'memory_percent': m.memory_percent,
        'disk_percent': m.disk_percent, 'load_1m': m.load_1m,
        'network_rx_bytes': m.network_rx_bytes, 'network_tx_bytes': m.network_tx_bytes,
    } for m in rows]
    return Response(data)


@api_view(['GET'])
def host_live_processes(request, host_id):
    """Return a live process list for a host (on-demand)."""
    try:
        host = Host.objects.get(pk=host_id)
    except Host.DoesNotExist:
        return Response({'detail': 'host not found'}, status=status.HTTP_404_NOT_FOUND)
    try:
        processes = collect_processes(host)
        HostProcess.objects.create(host_id=host.id, host_name=host.name, processes=processes)
        return Response(processes)
    except Exception as exc:
        return Response({'detail': f'{type(exc).__name__}: {exc}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def trigger_collect(request, host_id):
    """Trigger an async metric collection for a host."""
    collect_host_metrics.delay(host_id)
    collect_host_processes.delay(host_id)
    return Response({'ok': True})
