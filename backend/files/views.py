import io
import os
import uuid
from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from hosts.models import Host
from .models import UploadedFile, FileTransfer
from .serializers import UploadedFileSerializer, FileTransferSerializer
from .sftp import list_dir, read_file, write_file, delete_path
from .tasks import run_file_transfer


class UploadedFileViewSet(viewsets.ModelViewSet):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    search_fields = ['name']

    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)
        rel_dir = 'uploads'
        abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        unique = f'{uuid.uuid4().hex}_{file.name}'
        rel_path = os.path.join(rel_dir, unique)
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        with open(abs_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        obj = UploadedFile.objects.create(name=file.name, size=file.size, path=rel_path,
                                          created_by=request.user)
        return Response(UploadedFileSerializer(obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        obj = self.get_object()
        path = os.path.join(settings.MEDIA_ROOT, obj.path)
        if not os.path.isfile(path):
            return Response({'detail': 'file not found'}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(path, 'rb'), as_attachment=True, filename=obj.name)


class FileTransferViewSet(viewsets.ModelViewSet):
    queryset = FileTransfer.objects.all()
    serializer_class = FileTransferSerializer

    def get_queryset(self):
        return super().get_queryset().select_related('created_by').prefetch_related('results')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transfer = serializer.save(created_by=request.user)
        run_file_transfer.delay(transfer.id)
        return Response(self.get_serializer(transfer).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def host_list_dir(request, host_id):
    path = request.query_params.get('path', '.')
    try:
        host = Host.objects.get(pk=host_id)
    except Host.DoesNotExist:
        return Response({'detail': 'host not found'}, status=status.HTTP_404_NOT_FOUND)
    try:
        items = list_dir(host, path)
        return Response(items)
    except Exception as exc:
        return Response({'detail': f'{type(exc).__name__}: {exc}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def host_download(request, host_id):
    path = request.query_params.get('path')
    if not path:
        return Response({'detail': 'path required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        host = Host.objects.get(pk=host_id)
        data = read_file(host, path)
        return FileResponse(io.BytesIO(data), as_attachment=True, filename=os.path.basename(path))
    except Exception as exc:
        return Response({'detail': f'{type(exc).__name__}: {exc}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def host_upload(request, host_id):
    path = request.data.get('path')
    file = request.FILES.get('file')
    if not path or not file:
        return Response({'detail': 'path and file required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        host = Host.objects.get(pk=host_id)
        write_file(host, path, file.read())
        return Response({'ok': True})
    except Exception as exc:
        return Response({'detail': f'{type(exc).__name__}: {exc}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def host_delete(request, host_id):
    path = request.data.get('path')
    if not path:
        return Response({'detail': 'path required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        host = Host.objects.get(pk=host_id)
        delete_path(host, path)
        return Response({'ok': True})
    except Exception as exc:
        return Response({'detail': f'{type(exc).__name__}: {exc}'}, status=status.HTTP_400_BAD_REQUEST)
