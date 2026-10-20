from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppViewSet, BuildRepositoryViewSet, ReleaseViewSet, webhook_release

router = DefaultRouter()
router.register('apps', AppViewSet, basename='app')
router.register('repositories', BuildRepositoryViewSet, basename='build-repository')
router.register('releases', ReleaseViewSet, basename='release')

urlpatterns = [
    path('webhook/<int:app_id>/<str:token>/', webhook_release),
    path('', include(router.urls)),
]
