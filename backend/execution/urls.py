from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExecTemplateViewSet, ExecutionViewSet

router = DefaultRouter()
router.register('templates', ExecTemplateViewSet, basename='exec-template')
router.register('executions', ExecutionViewSet, basename='execution')

urlpatterns = [
    path('', include(router.urls)),
]
