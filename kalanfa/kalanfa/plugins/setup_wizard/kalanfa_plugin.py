from kalanfa.core.device.hooks import GetOSUserHook
from kalanfa.core.device.hooks import SetupHook
from kalanfa.core.webpack import hooks as webpack_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.utils import translation
from kalanfa.utils.translation import gettext as _


class SetupWizardPlugin(KalanfaPluginBase):
    untranslated_view_urls = "api_urls"
    translated_view_urls = "urls"

    @property
    def url_slug(self):
        return "setup"

    def name(self, lang):
        with translation.override(lang):
            return _("Setup Wizard")


@register_hook
class SetupWizardAsset(webpack_hooks.WebpackBundleHook):
    bundle_id = "app"

    @property
    def plugin_data(self):
        return {
            "canGetOSUser": GetOSUserHook.is_registered,
        }


@register_hook
class SetupWizardHook(SetupHook):
    @property
    def url(self):
        return self.plugin_url(SetupWizardPlugin, "setupwizard")
