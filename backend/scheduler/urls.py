from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScheduledTaskViewSet

router = DefaultRouter()
router.register('tasks', ScheduledTaskViewSet, basename='scheduled-task')

urlpatterns = [
    path('', include(router.urls)),
]
