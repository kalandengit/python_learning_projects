import logging
import os

from magicbus.plugins import SimplePlugin
from magicbus.plugins.tasks import Autoreloader

from kalanfa.core.content.hooks import ShareFileHook
from kalanfa.core.device.hooks import CheckIsMeteredHook
from kalanfa.core.device.hooks import GetOSUserHook
from kalanfa.core.tasks.hooks import JobHook
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook
from kalanfa.utils.server.hooks import KalanfaProcessHook

logger = logging.getLogger(__name__)


class ExampleAppPlugin(KalanfaPluginBase):
    pass


@register_hook
class ExampleAppGetOSUserHook(GetOSUserHook):
    def get_os_user(self, auth_token):
        return "os_user", True


@register_hook
class ExampleAppCheckIsMeteredHook(CheckIsMeteredHook):
    def check_is_metered(self):
        return True


@register_hook
class ExampleAppShareFileHook(ShareFileHook):
    def share_file(self, file_path, message):
        logger.debug(f"Sharing file {file_path} with message {message}")


@register_hook
class ExampleAppJobHook(JobHook):
    def schedule(self, job, orm_job):
        logger.debug(f"Scheduling job {job} with ORM job {orm_job}")

    def update(self, job, orm_job, state=None, **kwargs):
        from kalanfa.core.tasks.job import log_status

        log_status(job, orm_job, state=state, **kwargs)

    def clear(self, job, orm_job):
        logger.debug(f"Clearing job {job} with ORM job {orm_job}")


class AppUrlLoggerPlugin(SimplePlugin):
    def SERVING(self, port):
        self.port = port

    def RUN(self):
        from kalanfa.core.device.utils import app_initialize_url

        start_url = "http://127.0.0.1:{port}".format(
            port=self.port
        ) + app_initialize_url(auth_token="1234")
        # Use warning to make sure this message stands out in the console
        logger.warning(
            "Open this URL to activate app mode: {start_url}".format(
                start_url=start_url
            )
        )


@register_hook
class DeveloperAppUrlLogger(KalanfaProcessHook):
    MagicBusPluginClass = AppUrlLoggerPlugin


class KalanfaAutoReloader(Autoreloader):
    def __init__(self, bus):
        super().__init__(bus)
        from kalanfa.utils import conf

        plugins = os.path.join(conf.KALANFA_HOME, "plugins.json")
        options = os.path.join(conf.KALANFA_HOME, "options.ini")
        self.files.add(plugins)
        self.files.add(options)


@register_hook
class KalanfaAutoReloadHook(KalanfaProcessHook):
    MagicBusPluginClass = KalanfaAutoReloader
