from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HostViewSet, HostGroupViewSet, CredentialViewSet

router = DefaultRouter()
router.register('hosts', HostViewSet, basename='host')
router.register('groups', HostGroupViewSet, basename='host-group')
router.register('credentials', CredentialViewSet, basename='credential')

urlpatterns = [
    path('', include(router.urls)),
]
