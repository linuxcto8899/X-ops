from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse


def health(request):
    return JsonResponse({'ok': True, 'service': 'ops-platform'})


router = DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('accounts.urls')),
    path('api/hosts/', include('hosts.urls')),
    path('api/exec/', include('execution.urls')),
    path('api/files/', include('files.urls')),
    path('api/deploy/', include('deploy.urls')),
    path('api/pipeline/', include('pipeline.urls')),
    path('api/monitor/', include('monitor.urls')),
    path('api/scheduler/', include('scheduler.urls')),
    path('api/config/', include('config_center.urls')),
    path('api/', include(router.urls)),
]
