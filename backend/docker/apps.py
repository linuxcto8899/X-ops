from django.apps import AppConfig


class DockerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'docker'
    verbose_name = 'Docker 管理'