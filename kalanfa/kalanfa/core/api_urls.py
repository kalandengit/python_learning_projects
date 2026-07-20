"""
Kalanfa Core API URL Configuration.

WARNING: These APIs are internal and designed for Kalanfa's own frontend.
They may change without notice between releases. Do not build external
applications that depend on these endpoints.

For stable APIs, use only the /public/ endpoints defined in
kalanfa.core.public.api_urls - these are maintained with backwards
compatibility for external integrations.
"""

from django.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r"^auth/", include("kalanfa.core.auth.api_urls")),
    re_path(r"^bookmarks/", include("kalanfa.core.bookmarks.api_urls")),
    re_path(r"^content/", include("kalanfa.core.content.api_urls")),
    re_path(r"^logger/", include("kalanfa.core.logger.api_urls")),
    re_path(r"^tasks/", include("kalanfa.core.tasks.api_urls")),
    re_path(r"^exams/", include("kalanfa.core.exams.api_urls")),
    re_path(r"^device/", include("kalanfa.core.device.api_urls")),
    re_path(r"^lessons/", include("kalanfa.core.lessons.api_urls")),
    re_path(r"^courses/", include("kalanfa.core.courses.api_urls")),
    re_path(r"^discovery/", include("kalanfa.core.discovery.api_urls")),
    re_path(r"^notifications/", include("kalanfa.core.analytics.api_urls")),
    re_path(r"^attendance/", include("kalanfa.core.attendance.api_urls")),
    re_path(r"^public/", include("kalanfa.core.public.api_urls")),
]
