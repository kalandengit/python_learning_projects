from le_utils.constants import format_presets

from kalanfa.core.content import hooks as content_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook


class QTIViewerPlugin(KalanfaPluginBase):
    pass


@register_hook
class QTIViewerAsset(content_hooks.ContentRendererHook):
    bundle_id = "main"
    presets = (format_presets.QTI_ZIP,)
