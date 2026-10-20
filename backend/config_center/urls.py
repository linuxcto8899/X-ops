from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EnvViewSet, ServiceViewSet, AppConfigViewSet, open_api

router = DefaultRouter()
router.register('envs', EnvViewSet, basename='env')
router.register('services', ServiceViewSet, basename='service')
router.register('configs', AppConfigViewSet, basename='app-config')

urlpatterns = [
    path('open/<str:service>/<str:env>/', open_api),
    path('', include(router.urls)),
]
