from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Pipeline, PipelineRun
from .serializers import PipelineSerializer, PipelineRunSerializer
from .executor import run_pipeline


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    search_fields = ['name', 'description']

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        pipeline = self.get_object()
        if not pipeline.enabled:
            return Response({'detail': 'pipeline is disabled'}, status=status.HTTP_400_BAD_REQUEST)
        run_obj = PipelineRun.objects.create(pipeline=pipeline, created_by=request.user,
                                             params=request.data.get('params', {}))
        # Execute synchronously for now (could be moved to Celery)
        run_pipeline(run_obj)
        return Response(PipelineRunSerializer(run_obj).data, status=status.HTTP_201_CREATED)


class PipelineRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PipelineRun.objects.all()
    serializer_class = PipelineRunSerializer
    filterset_fields = ['pipeline', 'status']

    def get_queryset(self):
        return super().get_queryset().select_related('pipeline', 'created_by')
