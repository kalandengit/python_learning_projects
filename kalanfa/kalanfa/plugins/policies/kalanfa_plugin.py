from kalanfa.core.webpack import hooks as webpack_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.utils import translation
from kalanfa.utils.translation import gettext as _


class Policies(KalanfaPluginBase):
    translated_view_urls = "urls"

    @property
    def url_slug(self):
        return "policies"

    def name(self, lang):
        with translation.override(lang):
            return _("Policies")


@register_hook
class PoliciesAsset(webpack_hooks.WebpackBundleHook):
    bundle_id = "app"
