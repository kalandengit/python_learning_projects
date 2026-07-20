"""
This is here to enable redirects from the old /user endpoint to /auth
"""

from django.urls import include
from django.urls import re_path
from django.views.generic.base import RedirectView

from kalanfa.core.device.translation import i18n_patterns

redirect_patterns = [
    re_path(
        r"^user/$",
        RedirectView.as_view(
            pattern_name="kalanfa:kalanfa.plugins.user_auth:user_auth", permanent=True
        ),
        name="redirect_user",
    ),
]

urlpatterns = [re_path(r"", include(i18n_patterns(redirect_patterns)))]
