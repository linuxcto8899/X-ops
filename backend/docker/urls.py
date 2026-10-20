from django.urls import path
from . import views

urlpatterns = [
    path('host/<int:host_id>/info/', views.info),
    path('host/<int:host_id>/containers/', views.containers),
    path('host/<int:host_id>/containers/<str:container_id>/logs/', views.container_logs),
    path('host/<int:host_id>/containers/<str:container_id>/<str:action>/', views.container_action),
    path('host/<int:host_id>/images/', views.images),
    path('host/<int:host_id>/images/<str:image_ref>/remove/', views.remove_image),
    path('host/<int:host_id>/networks/', views.networks),
]