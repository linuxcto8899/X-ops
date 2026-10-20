import secrets
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import App, Release, ReleaseApproval, BuildRepository
from .serializers import (AppSerializer, ReleaseSerializer, ReleaseApprovalSerializer,
                          BuildRepositorySerializer)
from .tasks import execute_release, rollback_release


class AppViewSet(viewsets.ModelViewSet):
    queryset = App.objects.all()
    serializer_class = AppSerializer
    search_fields = ['name', 'description']


class BuildRepositoryViewSet(viewsets.ModelViewSet):
    queryset = BuildRepository.objects.all()
    serializer_class = BuildRepositorySerializer
    search_fields = ['name']


class ReleaseViewSet(viewsets.ModelViewSet):
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer
    filterset_fields = ['app', 'status']

    def get_queryset(self):
        return super().get_queryset().select_related('app', 'created_by').prefetch_related('results')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        release = serializer.save(created_by=request.user)
        app = release.app
        if app.approval_required:
            release.status = 'wait_approval'
            release.save(update_fields=['status'])
        else:
            _launch(release)
        return Response(self.get_serializer(release).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        release = self.get_object()
        _launch(release)
        return Response(ReleaseSerializer(release).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        release = self.get_object()
        if release.status != 'wait_approval':
            return Response({'detail': 'release is not waiting approval'}, status=status.HTTP_400_BAD_REQUEST)
        ReleaseApproval.objects.create(release=release, decision='approved',
                                       comment=request.data.get('comment', ''),
                                       decided_by=request.user)
        _launch(release)
        return Response(ReleaseSerializer(release).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        release = self.get_object()
        ReleaseApproval.objects.create(release=release, decision='rejected',
                                       comment=request.data.get('comment', ''),
                                       decided_by=request.user)
        release.status = 'cancelled'
        release.save(update_fields=['status'])
        return Response(ReleaseSerializer(release).data)

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        release = self.get_object()
        rollback_release.delay(release.id)
        return Response({'ok': True})

    @action(detail=True, methods=['post'])
    def gen_webhook(self, request, pk=None):
        release = self.get_object()
        release.webhook_token = secrets.token_urlsafe(32)
        release.save(update_fields=['webhook_token'])
        return Response({'webhook_token': release.webhook_token})


def _launch(release):
    if release.schedule_at and release.schedule_at > timezone.now():
        release.status = 'pending'
        release.save(update_fields=['status'])
        return
    release.status = 'releasing'
    release.save(update_fields=['status'])
    execute_release.delay(release.id)


@api_view(['POST'])
@permission_classes([AllowAny])
def webhook_release(request, app_id, token):
    """Webhook auto-release: POST /api/deploy/webhook/<app_id>/<token>/"""
    try:
        app = App.objects.get(pk=app_id)
    except App.DoesNotExist:
        return Response({'detail': 'not found'}, status=status.HTTP_404_NOT_FOUND)
    version = request.data.get('version', '') or request.query_params.get('version', '')
    release = Release.objects.create(app=app, version=version or f'webhook-{timezone.now():%Y%m%d%H%M%S}')
    _launch(release)
    return Response({'ok': True, 'release_id': release.id}, status=status.HTTP_201_CREATED)
