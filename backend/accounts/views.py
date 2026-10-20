from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import User, Role
from .serializers import UserSerializer, RoleSerializer, MeSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'phone']
    filterset_fields = ['role', 'is_active']


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    return Response(MeSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    user = request.user
    old = request.data.get('old_password')
    new = request.data.get('new_password')
    if not user.check_password(old):
        return Response({'detail': 'Old password is incorrect.'}, status=400)
    if not new or len(new) < 8:
        return Response({'detail': 'New password must be at least 8 characters.'}, status=400)
    user.set_password(new)
    user.save()
    return Response({'ok': True})
