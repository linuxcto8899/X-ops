from rest_framework import serializers
from .models import ScheduledTask, TaskRunRecord
from .cron import parse_cron
from .tasks import compute_next_run


class TaskRunRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskRunRecord
        fields = ['id', 'status', 'output', 'error', 'created_at']


class ScheduledTaskSerializer(serializers.ModelSerializer):
    runs = TaskRunRecordSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = ScheduledTask
        fields = ['id', 'name', 'trigger', 'cron', 'interval', 'run_at', 'monitor_rule_id',
                  'command', 'host_ids', 'run_local', 'enabled', 'last_run_at', 'next_run_at',
                  'runs', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'last_run_at', 'next_run_at', 'runs', 'created_at']

    def validate(self, attrs):
        trigger = attrs.get('trigger', getattr(self.instance, 'trigger', None))
        if trigger == 'cron':
            cron = attrs.get('cron', getattr(self.instance, 'cron', ''))
            try:
                parse_cron(cron)
            except ValueError as exc:
                raise serializers.ValidationError({'cron': str(exc)})
        return attrs

    def create(self, validated_data):
        task = super().create(validated_data)
        task.next_run_at = compute_next_run(task)
        task.save(update_fields=['next_run_at'])
        return task

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.next_run_at = compute_next_run(instance)
        instance.save(update_fields=['next_run_at'])
        return instance
