from django.urls import reverse
from le_utils.constants import modalities

from kalanfa.core.auth.constants.user_kinds import ANONYMOUS
from kalanfa.core.auth.constants.user_kinds import LEARNER
from kalanfa.core.content.hooks import ContentNodeDisplayHook
from kalanfa.core.content.hooks import ShareFileHook
from kalanfa.core.device.hooks import CheckIsMeteredHook
from kalanfa.core.device.utils import allow_learner_unassigned_resource_access
from kalanfa.core.device.utils import allow_other_browsers_to_connect
from kalanfa.core.device.utils import get_device_setting
from kalanfa.core.device.utils import is_landing_page
from kalanfa.core.device.utils import LANDING_PAGE_LEARN
from kalanfa.core.discovery.hooks import NetworkLocationBroadcastHook
from kalanfa.core.discovery.hooks import NetworkLocationDiscoveryHook
from kalanfa.core.hooks import NavigationHook
from kalanfa.core.hooks import RoleBasedRedirectHook
from kalanfa.core.utils.lock import retry_on_db_lock
from kalanfa.core.webpack import hooks as webpack_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.utils import conf
from kalanfa.utils import translation
from kalanfa.utils.translation import gettext as _


class Learn(KalanfaPluginBase):
    untranslated_view_urls = "api_urls"
    translated_view_urls = "urls"
    kalanfa_options = "options"
    can_manage_while_running = True

    def name(self, lang):
        with translation.override(lang):
            return _("Learn")


@register_hook
class LearnRedirect(RoleBasedRedirectHook):
    @property
    def roles(self):
        if is_landing_page(LANDING_PAGE_LEARN):
            return (ANONYMOUS, LEARNER)

        return (LEARNER,)

    @property
    def url(self):
        return self.plugin_url(Learn, "learn")


@register_hook
class LearnNavItem(NavigationHook):
    bundle_id = "side_nav"


@register_hook
class LearnAsset(webpack_hooks.WebpackBundleHook):
    bundle_id = "app"

    @property
    def plugin_data(self):
        from kalanfa.core.content.models import ContentNode
        from kalanfa.core.discovery.well_known import CENTRAL_CONTENT_BASE_INSTANCE_ID
        from kalanfa.core.discovery.well_known import CENTRAL_CONTENT_BASE_URL

        courses_exist = ContentNode.objects.filter(
            available=True, modality=modalities.COURSE
        ).exists()

        return {
            "allowDownloadOnMeteredConnection": get_device_setting(
                "allow_download_on_metered_connection"
            ),
            "canCheckMeteredConnection": CheckIsMeteredHook.is_registered,
            "canShareFile": ShareFileHook.is_registered,
            "allowGuestAccess": get_device_setting("allow_guest_access"),
            "allowLearnerDownloads": get_device_setting(
                "allow_learner_download_resources"
            ),
            "allowLearnerUnassignedResourceAccess": allow_learner_unassigned_resource_access(),
            "allowRemoteAccess": allow_other_browsers_to_connect(),
            "enableCustomChannelNav": conf.OPTIONS["Learn"][
                "ENABLE_CUSTOM_CHANNEL_NAV"
            ],
            "studioDevice": {
                "base_url": CENTRAL_CONTENT_BASE_URL,
                "instance_id": CENTRAL_CONTENT_BASE_INSTANCE_ID,
            },
            "courses_exist": courses_exist,
        }


@register_hook
class MyDownloadsAsset(webpack_hooks.WebpackBundleHook):
    bundle_id = "my_downloads_app"

    @property
    def plugin_data(self):
        return {
            "setLimitForAutodownload": get_device_setting("set_limit_for_autodownload"),
            "limitForAutodownload": get_device_setting("limit_for_autodownload"),
        }


@register_hook
class LearnContentNodeHook(ContentNodeDisplayHook):
    def node_url(self, node):
        kind_slug = None
        if not node.parent:
            kind_slug = ""
        elif node.kind == "topic":
            kind_slug = "t/"
        else:
            kind_slug = "c/"
        if kind_slug is not None:
            return (
                reverse("kalanfa:kalanfa.plugins.learn:learn")
                + "#/topics/"
                + kind_slug
                + node.id
            )


@retry_on_db_lock
def request_soud_sync(network_location):
    """
    :type network_location: kalanfa.core.discovery.models.NetworkLocation
    """
    from kalanfa.core.auth.tasks import enqueue_soud_sync_processing
    from kalanfa.core.device.soud import request_sync_hook

    if not network_location.subset_of_users_device and network_location.is_kalanfa:
        request_sync_hook(network_location)
        enqueue_soud_sync_processing()


@register_hook
class NetworkDiscoveryForSoUDHook(NetworkLocationDiscoveryHook):
    def on_connect(self, network_location):
        """
        :type network_location: kalanfa.core.discovery.models.NetworkLocation
        """
        if get_device_setting("subset_of_users_device"):
            request_soud_sync(network_location)


@register_hook
class NetworkBroadcastForSoUDHook(NetworkLocationBroadcastHook):
    """
    This hook is used to hook into the broadcast of the SoUD status of this device to other
    devices on the network. So when this device is updated, possibly to SoUD, it will
    enqueue SoUD syncs to all other non-SoUD devices on the network.
    """

    def on_renew(self, instance, network_locations):
        """
        :type instance: kalanfa.core.discovery.utils.network.broadcast.KalanfaInstance
        :type network_locations: kalanfa.core.discovery.models.NetworkLocation[]
        """
        if not get_device_setting("subset_of_users_device"):
            return

        for network_location in network_locations:
            request_soud_sync(network_location)


@register_hook
class MyDownloadsNavAction(NavigationHook):
    bundle_id = "my_downloads_side_nav"

    @property
    def plugin_data(self):
        return {
            "allowLearnerDownloads": get_device_setting(
                "allow_learner_download_resources"
            ),
        }
