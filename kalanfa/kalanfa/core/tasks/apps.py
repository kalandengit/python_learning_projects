from django.apps import AppConfig


class KalanfaTasksConfig(AppConfig):
    name = "kalanfa.core.tasks"
    label = "kalanfatasks"
    verbose_name = "Kalanfa Tasks"

    def ready(self):
        pass
