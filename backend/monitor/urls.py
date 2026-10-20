from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (HostMetricViewSet, HostProcessViewSet, MonitorRuleViewSet,
                    MonitorRecordViewSet, AlertContactViewSet, AlertGroupViewSet,
                    AlertRecordViewSet, NotifyChannelViewSet, host_live_metrics,
                    host_metric_history, host_live_processes, trigger_collect)

router = DefaultRouter()
router.register('metrics', HostMetricViewSet, basename='host-metric')
router.register('processes', HostProcessViewSet, basename='host-process')
router.register('rules', MonitorRuleViewSet, basename='monitor-rule')
router.register('records', MonitorRecordViewSet, basename='monitor-record')
router.register('contacts', AlertContactViewSet, basename='alert-contact')
router.register('groups', AlertGroupViewSet, basename='alert-group')
router.register('alerts', AlertRecordViewSet, basename='alert-record')
router.register('channels', NotifyChannelViewSet, basename='notify-channel')

urlpatterns = [
    path('host/<int:host_id>/live/', host_live_metrics),
    path('host/<int:host_id>/history/', host_metric_history),
    path('host/<int:host_id>/processes/', host_live_processes),
    path('host/<int:host_id>/collect/', trigger_collect),
    path('', include(router.urls)),
]
