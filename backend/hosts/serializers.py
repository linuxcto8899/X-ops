from rest_framework import serializers
from .models import Host, HostGroup, Credential


class HostGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostGroup
        fields = ['id', 'name', 'parent', 'description', 'created_at']


class CredentialSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    private_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    key_passphrase = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Credential
        fields = ['id', 'name', 'username', 'password', 'private_key', 'key_passphrase',
                  'description', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', '')
        private_key = validated_data.pop('private_key', '')
        passphrase = validated_data.pop('key_passphrase', '')
        obj = Credential.objects.create(**validated_data)
        obj.set_password(password)
        obj.set_private_key(private_key)
        obj.set_key_passphrase(passphrase)
        obj.save()
        return obj

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        private_key = validated_data.pop('private_key', None)
        passphrase = validated_data.pop('key_passphrase', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password is not None:
            instance.set_password(password)
        if private_key is not None:
            instance.set_private_key(private_key)
        if passphrase is not None:
            instance.set_key_passphrase(passphrase)
        instance.save()
        return instance


class HostSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    private_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    key_passphrase = serializers.CharField(write_only=True, required=False, allow_blank=True)
    group_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Host
        fields = ['id', 'name', 'hostname', 'port', 'username', 'password', 'private_key',
                  'key_passphrase', 'credential', 'groups', 'group_ids', 'os_name', 'os_version',
                  'architecture', 'cpu_count', 'memory_mb', 'disk_total_gb', 'status',
                  'last_checked_at', 'last_connected_at', 'cloud_provider', 'region',
                  'region_code', 'expire_at', 'remark', 'created_at']
        read_only_fields = ['id', 'os_name', 'os_version', 'architecture', 'cpu_count',
                            'memory_mb', 'disk_total_gb', 'status', 'last_checked_at',
                            'last_connected_at', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', '')
        private_key = validated_data.pop('private_key', '')
        passphrase = validated_data.pop('key_passphrase', '')
        group_ids = validated_data.pop('group_ids', [])
        groups = validated_data.pop('groups', [])
        obj = Host.objects.create(**validated_data)
        obj.set_password(password)
        obj.set_private_key(private_key)
        obj.set_key_passphrase(passphrase)
        if groups:
            obj.groups.set(groups)
        elif group_ids:
            obj.groups.set(HostGroup.objects.filter(id__in=group_ids))
        obj.save()
        return obj

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        private_key = validated_data.pop('private_key', None)
        passphrase = validated_data.pop('key_passphrase', None)
        group_ids = validated_data.pop('group_ids', None)
        groups = validated_data.pop('groups', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password is not None:
            instance.set_password(password)
        if private_key is not None:
            instance.set_private_key(private_key)
        if passphrase is not None:
            instance.set_key_passphrase(passphrase)
        if groups is not None:
            instance.groups.set(groups)
        elif group_ids is not None:
            instance.groups.set(HostGroup.objects.filter(id__in=group_ids))
        instance.save()
        return instance
