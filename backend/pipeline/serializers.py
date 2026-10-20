from rest_framework import serializers
from .models import Pipeline, PipelineRun


class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'nodes', 'enabled', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PipelineRunSerializer(serializers.ModelSerializer):
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = PipelineRun
        fields = ['id', 'pipeline', 'pipeline_name', 'status', 'current_node',
                  'node_results', 'params', 'created_by', 'created_by_name',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'current_node', 'node_results', 'created_at', 'updated_at']
