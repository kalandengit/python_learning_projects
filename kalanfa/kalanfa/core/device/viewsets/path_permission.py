from rest_framework import views
from rest_framework.response import Response

from kalanfa.core.device.permissions import UserHasAnyDevicePermissions
from kalanfa.core.utils.drf_utils import swagger_auto_schema_available
from kalanfa.utils.conf import OPTIONS
from kalanfa.utils.filesystem import check_is_directory
from kalanfa.utils.filesystem import get_path_permission


class PathPermissionView(views.APIView):
    permission_classes = (UserHasAnyDevicePermissions,)

    @swagger_auto_schema_available(
        [("path", "path to check permissions for", "string")]
    )
    def get(self, request):
        pathname = request.query_params.get("path", OPTIONS["Paths"]["CONTENT_DIR"])
        return Response(
            {
                "writable": get_path_permission(pathname),
                "directory": check_is_directory(pathname),
                "path": pathname,
            }
        )
