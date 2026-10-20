from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (UploadedFileViewSet, FileTransferViewSet,
                    host_list_dir, host_download, host_upload, host_delete)

router = DefaultRouter()
router.register('uploads', UploadedFileViewSet, basename='uploaded-file')
router.register('transfers', FileTransferViewSet, basename='file-transfer')

urlpatterns = [
    path('host/<int:host_id>/list/', host_list_dir),
    path('host/<int:host_id>/download/', host_download),
    path('host/<int:host_id>/upload/', host_upload),
    path('host/<int:host_id>/delete/', host_delete),
    path('', include(router.urls)),
]
