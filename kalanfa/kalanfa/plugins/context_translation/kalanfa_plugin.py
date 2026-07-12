from django.templatetags.static import static
from django.utils.safestring import mark_safe

from kalanfa.core.hooks import FrontEndBaseHeadHook
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook


class ContextTranslationPlugin(KalanfaPluginBase):
    """
    A plugin to enable support for translating the user interface of Kalanfa
    using Crowdin's in-context translation feature.
    """

    kalanfa_option_defaults = "option_defaults"
    django_settings = "settings"


@register_hook
class JIPTHeadHook(FrontEndBaseHeadHook):
    @property
    def head_html(self):
        js_url = static("assets/context_translation/jipt.js")
        return mark_safe(
            "\n".join(
                [
                    f"""<script type="text/javascript" src="{js_url}"></script>""",
                    """<script type="text/javascript" src="https://cdn.crowdin.com/jipt/jipt.js"></script>""",
                ]
            )
        )
