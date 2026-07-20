from django.apps import AppConfig


class KalanfaLoggerConfig(AppConfig):
    name = "kalanfa.core.logger"
    label = "logger"
    verbose_name = "Kalanfa Logger"

    def ready(self):
        pass
