from kalanfa.core.hooks import FrontEndBaseSyncHook
from kalanfa.core.webpack.hooks import WebpackBundleHook
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.utils import conf


class SentryPlugin(KalanfaPluginBase):
    django_settings = "settings"
    kalanfa_options = "options"


@register_hook
class SentryPluginAsset(WebpackBundleHook):
    bundle_id = "main"

    @property
    def plugin_data(self):
        return {
            "sentryDSN": conf.OPTIONS["Debug"]["SENTRY_FRONTEND_DSN"],
            "sentryEnv": conf.OPTIONS["Debug"]["SENTRY_ENVIRONMENT"],
            "sentryReplayEnabled": conf.OPTIONS["Debug"]["SENTRY_REPLAY_ENABLED"],
        }


@register_hook
class SentryPluginInclusionHook(FrontEndBaseSyncHook):
    bundle_class = SentryPluginAsset
