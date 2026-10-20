from rest_framework import serializers
from .models import App, Release, ReleaseApproval, ReleaseResult, BuildRepository


class AppSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ['id', 'name', 'mode', 'repo_url', 'repo_branch', 'build_command',
                  'deploy_script', 'host_ids', 'target_path', 'grayscale_enabled',
                  'grayscale_percent', 'build_separate', 'approval_required',
                  'description', 'created_at', 'updated_at']


class ReleaseResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseResult
        fields = ['id', 'host_id', 'host_name', 'status', 'output', 'error']


class ReleaseSerializer(serializers.ModelSerializer):
    app_name = serializers.CharField(source='app.name', read_only=True)
    results = ReleaseResultSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = Release
        fields = ['id', 'app', 'app_name', 'version', 'status', 'schedule_at',
                  'build_log', 'release_log', 'grayscale', 'webhook_token',
                  'results', 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'build_log', 'release_log', 'results',
                            'created_at', 'updated_at']


class ReleaseApprovalSerializer(serializers.ModelSerializer):
    decided_by_name = serializers.CharField(source='decided_by.username', read_only=True, default=None)

    class Meta:
        model = ReleaseApproval
        fields = ['id', 'release', 'decision', 'comment', 'decided_by', 'decided_by_name', 'decided_at']
        read_only_fields = ['id', 'release', 'decided_by', 'decided_at']


class BuildRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildRepository
        fields = ['id', 'name', 'url', 'credential_id', 'created_at']
