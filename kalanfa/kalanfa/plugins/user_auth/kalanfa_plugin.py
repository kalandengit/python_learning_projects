from kalanfa.core.auth.constants.user_kinds import ANONYMOUS
from kalanfa.core.device.utils import allow_other_browsers_to_connect
from kalanfa.core.device.utils import get_device_setting
from kalanfa.core.device.utils import get_device_unusable_reason
from kalanfa.core.device.utils import is_landing_page
from kalanfa.core.device.utils import LANDING_PAGE_LEARN
from kalanfa.core.hooks import NavigationHook
from kalanfa.core.hooks import RoleBasedRedirectHook
from kalanfa.core.oidc_provider_hook import OIDCProviderHook
from kalanfa.core.webpack import hooks as webpack_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.plugins.user_auth.hooks import LoginItemHook


class UserAuth(KalanfaPluginBase):
    untranslated_view_urls = "api_urls"
    translated_view_urls = "urls"
    root_view_urls = "root_urls"

    @property
    def url_slug(self):
        return "auth"


@register_hook
class UserAuthAsset(webpack_hooks.WebpackBundleHook):
    bundle_id = "app"

    @property
    def plugin_data(self):
        return {
            "oidcProviderEnabled": OIDCProviderHook.is_enabled(),
            "allowGuestAccess": get_device_setting("allow_guest_access"),
            "allowRemoteAccess": allow_other_browsers_to_connect(),
            "deviceUnusableReason": get_device_unusable_reason(),
            "loginItems": [hook.data for hook in LoginItemHook.registered_hooks],
        }


@register_hook
class LogInRedirect(RoleBasedRedirectHook):
    @property
    def roles(self):
        if is_landing_page(LANDING_PAGE_LEARN):
            return (None,)

        return (ANONYMOUS,)

    @property
    def url(self):
        return self.plugin_url(UserAuth, "user_auth")


@register_hook
class LogInNavAction(NavigationHook):
    bundle_id = "login_side_nav"
