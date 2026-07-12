from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from kalanfa.core.oidc_provider_hook import OIDCProviderHook
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook


class OIDCProvider(KalanfaPluginBase):
    root_view_urls = "root_urls"
    django_settings = "settings"
    kalanfa_options = "options"

    @property
    def url_slug(self):
        return "^oidc_provider/"


@register_hook
class EnableOIDC(OIDCProviderHook):
    pass
