from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, Role


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8, trim_whitespace=False)
    role_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'roles', 'role_names',
                  'is_active', 'is_superuser', 'mfa_enabled', 'date_joined', 'password']
        read_only_fields = ['id', 'date_joined', 'mfa_enabled']

    def get_role_names(self, obj):
        return [r.name for r in obj.roles.all()]

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Password is required.'})
        if attrs.get('password'):
            try:
                validate_password(attrs['password'], user=self.instance)
            except Exception as exc:
                raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'perms', 'is_system', 'created_at']
        read_only_fields = ['id', 'created_at']


class MeSerializer(serializers.ModelSerializer):
    perms = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'is_superuser', 'mfa_enabled', 'perms']

    def get_perms(self, obj):
        perms = set()
        if obj.is_superuser or obj.role == 'admin':
            return ['*']
        for r in obj.roles.all():
            perms.update(r.perms or [])
        return sorted(perms)
