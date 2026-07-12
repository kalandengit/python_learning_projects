from rest_framework import serializers
from rest_framework import viewsets

from kalanfa.core.auth.models import FacilityUser
from kalanfa.core.auth.permissions import KalanfaAuthPermissions
from kalanfa.core.auth.permissions import KalanfaAuthPermissionsFilter
from kalanfa.core.device.models import DevicePermissions


class DevicePermissionsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=FacilityUser.objects.all())

    class Meta:
        model = DevicePermissions
        fields = ("user", "is_superuser", "can_manage_content")


class DevicePermissionsViewSet(viewsets.ModelViewSet):
    queryset = DevicePermissions.objects.all()
    serializer_class = DevicePermissionsSerializer
    permission_classes = (KalanfaAuthPermissions,)
    filter_backends = (KalanfaAuthPermissionsFilter,)
