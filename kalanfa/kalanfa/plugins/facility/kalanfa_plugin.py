from kalanfa.core.auth.constants.user_kinds import ADMIN
from kalanfa.core.hooks import NavigationHook
from kalanfa.core.hooks import RoleBasedRedirectHook
from kalanfa.core.webpack.hooks import WebpackBundleHook
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.utils import translation
from kalanfa.utils.translation import gettext as _


class FacilityManagementPlugin(KalanfaPluginBase):
    untranslated_view_urls = "api_urls"
    translated_view_urls = "urls"
    can_manage_while_running = True

    def name(self, lang):
        with translation.override(lang):
            return _("Facility")


@register_hook
class FacilityManagementAsset(WebpackBundleHook):
    bundle_id = "app"


@register_hook
class FacilityRedirect(RoleBasedRedirectHook):
    roles = (ADMIN,)
    require_full_facility = True
    require_no_on_my_own_facility = True

    @property
    def url(self):
        return self.plugin_url(FacilityManagementPlugin, "facility_management")


@register_hook
class FacilityManagementNavItem(NavigationHook):
    bundle_id = "side_nav"
