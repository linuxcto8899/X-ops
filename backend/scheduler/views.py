from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ScheduledTask
from .serializers import ScheduledTaskSerializer
from .tasks import run_scheduled_task


class ScheduledTaskViewSet(viewsets.ModelViewSet):
    queryset = ScheduledTask.objects.all()
    serializer_class = ScheduledTaskSerializer
    search_fields = ['name']
    filterset_fields = ['trigger', 'enabled']

    def get_queryset(self):
        return super().get_queryset().select_related('created_by').prefetch_related('runs')

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        task = self.get_object()
        run_scheduled_task.delay(task.id)
        return Response({'ok': True}, status=status.HTTP_202_ACCEPTED)
