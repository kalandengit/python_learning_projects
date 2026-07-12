import os

from .base import *  # noqa isort:skip @UnusedWildImport

DEBUG = True

# Settings might be tuples, so switch to lists
INSTALLED_APPS = list(INSTALLED_APPS) + ["drf_yasg", "silk"]  # noqa F405
webpack_middleware = "kalanfa.core.webpack.middleware.WebpackErrorHandler"
no_login_popup_middleware = (
    "kalanfa.core.auth.middleware.XhrPreventLoginPromptMiddleware"
)
silk_middleware = "silk.middleware.SilkyMiddleware"
MIDDLEWARE = list(MIDDLEWARE) + [  # noqa F405
    webpack_middleware,
    no_login_popup_middleware,
    silk_middleware,
]

INTERNAL_IPS = ["127.0.0.1"]

ROOT_URLCONF = "kalanfa.deployment.default.dev_urls"

DEVELOPER_MODE = True
os.environ.update({"KALANFA_DEVELOPER_MODE": "True"})

# Django Silk profiling
SILKY_PYTHON_PROFILER = True
SILKY_AUTHENTICATION = False
SILKY_AUTHORISATION = False
# Limit stored requests in dev
SILKY_MAX_RECORDED_REQUESTS = 10**3
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10


REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": "kalanfa.core.auth.models.KalanfaAnonymousUser",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # Always keep this first, so that we consistently return 403 responses
        # when a request is unauthenticated.
        "rest_framework.authentication.SessionAuthentication",
        # Activate basic auth for external API testing tools
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "kalanfa.deployment.default.renderers.LightBrowsableAPIRenderer",
    ),
    "EXCEPTION_HANDLER": "kalanfa.core.utils.exception_handler.custom_exception_handler",
}

SWAGGER_SETTINGS = {"DEFAULT_INFO": "kalanfa.deployment.default.dev_urls.api_info"}

# Ensure that the CSP is set up to allow webpack-dev-server to be accessed during development
WEBPACK_DEV_SERVER_PORT = os.environ.get("WEBPACK_DEV_SERVER_PORT", "3000")
CSP_DEFAULT_SRC += (f"localhost:{WEBPACK_DEV_SERVER_PORT}", "ws:")  # noqa F405
CSP_SCRIPT_SRC += (f"localhost:{WEBPACK_DEV_SERVER_PORT}",)  # noqa F405
CSP_STYLE_SRC += (f"localhost:{WEBPACK_DEV_SERVER_PORT}",)  # noqa F405
