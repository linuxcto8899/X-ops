from rest_framework import serializers
from .models import Env, Service, AppConfig


class EnvSerializer(serializers.ModelSerializer):
    class Meta:
        model = Env
        fields = ['id', 'name', 'description', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'created_at']


class AppConfigSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    env_name = serializers.CharField(source='env.name', read_only=True)

    class Meta:
        model = AppConfig
        fields = ['id', 'service', 'service_name', 'env', 'env_name', 'key',
                  'value', 'view', 'description', 'updated_at', 'created_at']
        read_only_fields = ['id', 'updated_at', 'created_at']
