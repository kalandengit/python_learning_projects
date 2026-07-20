from kalanfa.core.hooks import NavigationHook
from kalanfa.core.webpack import hooks as webpack_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.utils import translation
from kalanfa.utils.translation import gettext as _


class UserProfile(KalanfaPluginBase):
    untranslated_view_urls = "api_urls"
    translated_view_urls = "urls"
    can_manage_while_running = True

    @property
    def url_slug(self):
        return "profile"

    def name(self, lang):
        with translation.override(lang):
            return _("User Profile")


@register_hook
class UserAuthAsset(webpack_hooks.WebpackBundleHook):
    bundle_id = "app"


@register_hook
class ProfileNavAction(NavigationHook):
    bundle_id = "user_profile_side_nav"
