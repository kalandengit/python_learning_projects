"""
Kalanfa core url patterns
=========================

This module should be the glue between all other url patterns.

Do NOT use kalanfa.deployment.default project's urlconf for such! That file can
be modified by users.

Reverse lookups
---------------

Kalanfa uses the ``'kalanfa'`` namespace. To point to something in Kalanfa, use
the following lookup pattern:

.. code-block:: html+django

    <!-- A built-in kalanfa URL -->
    {% url 'kalanfa:core:url_name' %}

    <!-- A plugin URL -->
    {% url 'kalanfa:pluginnamespace:url_name' %}


Defining URLs for plugins
-------------------------

Plugin classes can define url modules, and they will automatically be included.

Place a url.py and have your plugin's definition class's ``url_module`` method
return the module.
"""

from django.urls import include
from django.urls import re_path
from rest_framework import routers

from kalanfa.core.device.translation import i18n_patterns
from kalanfa.core.device.viewsets.plugins import PluginsViewSet
from kalanfa.plugins.utils.urls import get_urls as plugin_urls

from .views import GuestRedirectView
from .views import logout_view
from .views import RootURLRedirectView
from .views import set_language
from .views import StatusCheckView
from .views import UnsupportedBrowserView

app_name = "kalanfa"

router = routers.SimpleRouter()

router.register(r"plugins", PluginsViewSet, basename="plugins")

# Patterns that we want to prefix because they need access to the current language
lang_prefixed_patterns = [
    re_path(r"^i18n/setlang/$", set_language, name="set_language"),
    re_path(r"^logout/$", logout_view, name="logout"),
    re_path(r"^redirectuser/$", RootURLRedirectView.as_view(), name="redirect_user"),
    re_path(r"^guestaccess/$", GuestRedirectView.as_view(), name="guest"),
    re_path(r"^unsupported/$", UnsupportedBrowserView.as_view(), name="unsupported"),
    re_path(r"^$", RootURLRedirectView.as_view(), name="root_redirect"),
    re_path(r"^", include(router.urls)),
]

core_urlpatterns = (
    [
        re_path(r"^api/", include("kalanfa.core.api_urls")),
        re_path(r"", include(i18n_patterns(lang_prefixed_patterns))),
        re_path(r"", include("kalanfa.core.content.urls")),
        re_path(r"^status/", StatusCheckView.as_view(), name="status_check"),
    ],
    "core",
)


urlpatterns = [re_path(r"", include(core_urlpatterns))]

urlpatterns += plugin_urls()
