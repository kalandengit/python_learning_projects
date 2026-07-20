from kalanfa.core.webpack import hooks as webpack_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.plugins.user_auth import hooks


class DemoServer(KalanfaPluginBase):
    pass


@register_hook
class DemoServerAsset(webpack_hooks.WebpackBundleHook):
    bundle_id = "main"


@register_hook
class DemoServerInclusionHook(hooks.UserAuthSyncHook):
    bundle_class = DemoServerAsset
