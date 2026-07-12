from le_utils.constants import format_presets

from kalanfa.core.content import hooks as content_hooks
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook


class ExercisePerseusRenderPlugin(KalanfaPluginBase):
    pass


@register_hook
class ExercisePerseusRenderAsset(content_hooks.ContentRendererHook):
    bundle_id = "main"
    presets = (format_presets.EXERCISE,)
