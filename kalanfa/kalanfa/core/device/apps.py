from django.apps import AppConfig


class KalanfaDeviceAppConfig(AppConfig):
    name = "kalanfa.core.device"
    label = "device"
    verbose_name = "Kalanfa Device"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals  # noqa F401
