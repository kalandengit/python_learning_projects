from le_utils.constants import format_presets

from kalanfa.core.content import hooks as content_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook


class HTML5AppPlugin(KalanfaPluginBase):
    pass


@register_hook
class HTML5AppAsset(content_hooks.ContentRendererHook):
    bundle_id = "main"
    presets = (
        format_presets.HTML5_ZIP,
        format_presets.H5P_ZIP,
        format_presets.IMSCP_ZIP,
    )
