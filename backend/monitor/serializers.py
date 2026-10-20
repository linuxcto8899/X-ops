from rest_framework import serializers
from .models import (HostMetric, HostProcess, MonitorRule, MonitorRecord,
                     AlertContact, AlertGroup, AlertRecord, NotifyChannel)


class HostMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostMetric
        fields = ['id', 'host_id', 'host_name', 'cpu_percent', 'memory_percent',
                  'memory_used_mb', 'memory_total_mb', 'disk_percent', 'disk_used_gb',
                  'disk_total_gb', 'network_rx_bytes', 'network_tx_bytes',
                  'load_1m', 'load_5m', 'load_15m', 'captured_at']


class HostProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostProcess
        fields = ['id', 'host_id', 'host_name', 'processes', 'captured_at']


class MonitorRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitorRule
        fields = ['id', 'name', 'type', 'target', 'port', 'host', 'interval',
                  'enabled', 'notify_group_id', 'created_at']


class MonitorRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitorRecord
        fields = ['id', 'rule', 'ok', 'detail', 'created_at']


class AlertContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertContact
        fields = ['id', 'name', 'channels', 'created_at']


class AlertGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertGroup
        fields = ['id', 'name', 'contacts', 'created_at']


class AlertRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRecord
        fields = ['id', 'rule', 'title', 'content', 'level', 'status', 'created_at']


class NotifyChannelSerializer(serializers.ModelSerializer):
    kind_name = serializers.CharField(source='get_kind_display', read_only=True)

    class Meta:
        model = NotifyChannel
        fields = ['id', 'name', 'kind', 'kind_name', 'config', 'enabled', 'created_at']
