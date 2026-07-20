import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

import kalanfa
from kalanfa.utils import conf
from kalanfa.utils.server import installation_type

sentry_sdk.init(
    dsn=conf.OPTIONS["Debug"]["SENTRY_BACKEND_DSN"],
    environment=conf.OPTIONS["Debug"]["SENTRY_ENVIRONMENT"],
    integrations=[DjangoIntegration()],
    release=kalanfa.__version__,
)

with sentry_sdk.configure_scope() as scope:
    scope.set_tag("mode", conf.OPTIONS["Deployment"]["RUN_MODE"])
    scope.set_tag("installer", installation_type())


# Copy of the Kalanfa default src directive plus sentry.io for sending error reports.
CSP_CONNECT_SRC = ("'self'", "data:", "blob:", "*.sentry.io") + tuple(
    conf.OPTIONS["Deployment"]["CSP_HOST_SOURCES"]
)
