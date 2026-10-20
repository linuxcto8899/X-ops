from rest_framework import serializers
from .models import ExecTemplate, Execution, ExecutionResult, ExecutionStream


class ExecTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecTemplate
        fields = ['id', 'name', 'language', 'content', 'params', 'description', 'created_at']


class ExecutionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionResult
        fields = ['id', 'host_id', 'host_name', 'exit_code', 'stdout', 'stderr',
                  'status', 'error', 'duration_ms']


class ExecutionStreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionStream
        fields = ['id', 'host_id', 'host_name', 'output', 'status', 'exit_code',
                  'error', 'started_at', 'finished_at']


class ExecutionSerializer(serializers.ModelSerializer):
    results = ExecutionResultSerializer(many=True, read_only=True)
    streams = ExecutionStreamSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = Execution
        fields = ['id', 'template', 'language', 'command', 'host_ids', 'status',
                  'results', 'streams', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'status', 'results', 'streams', 'created_at']