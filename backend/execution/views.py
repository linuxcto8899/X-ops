from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ExecTemplate, Execution, ExecutionStream
from .serializers import (ExecTemplateSerializer, ExecutionSerializer,
                          ExecutionStreamSerializer)
from .tasks import run_batch_execution


class ExecTemplateViewSet(viewsets.ModelViewSet):
    queryset = ExecTemplate.objects.all()
    serializer_class = ExecTemplateSerializer
    search_fields = ['name', 'description']
    filterset_fields = ['language']


class ExecutionViewSet(viewsets.ModelViewSet):
    queryset = Execution.objects.all()
    serializer_class = ExecutionSerializer
    search_fields = ['command']

    def get_queryset(self):
        return (super().get_queryset()
                .select_related('created_by')
                .prefetch_related('results', 'streams'))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        execution = serializer.save(created_by=request.user)
        run_batch_execution.delay(execution.id)
        return Response(self.get_serializer(execution).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        execution = self.get_object()
        return Response(ExecutionSerializer(execution).data['results'])

    @action(detail=True, methods=['get'])
    def streams(self, request, pk=None):
        execution = self.get_object()
        streams = ExecutionStream.objects.filter(execution=execution)
        return Response(ExecutionStreamSerializer(streams, many=True).data)
