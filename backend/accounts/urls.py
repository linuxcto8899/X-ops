from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RoleViewSet, me, change_password

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('roles', RoleViewSet, basename='role')

urlpatterns = [
    path('me/', me),
    path('change-password/', change_password),
    path('', include(router.urls)),
]
