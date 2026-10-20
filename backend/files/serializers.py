from rest_framework import serializers
from .models import UploadedFile, FileTransfer, FileTransferResult


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'name', 'size', 'path', 'created_at']


class FileTransferResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileTransferResult
        fields = ['id', 'host_id', 'host_name', 'status', 'error']


class FileTransferSerializer(serializers.ModelSerializer):
    results = FileTransferResultSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = FileTransfer
        fields = ['id', 'kind', 'uploaded_file', 'source_path', 'target_path', 'host_ids',
                  'status', 'results', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'status', 'results', 'created_at']
