from django.apps import AppConfig


class KalanfaAuthConfig(AppConfig):
    name = "kalanfa.core.auth"
    label = "kalanfaauth"
    verbose_name = "Kalanfa Auth"

    def ready(self):
        from morango.api.viewsets import session_controller  # noqa: F401

        from kalanfa.core.auth.sync_event_hook_utils import (
            post_sync_transfer_handler,
        )  # noqa: F401
        from kalanfa.core.auth.sync_event_hook_utils import (
            pre_sync_transfer_handler,
        )  # noqa: F401

        from .signals import cascade_delete_membership  # noqa: F401
        from .signals import cascade_delete_user  # noqa: F401

        # attach to `initializing.completed` signal so that the context has all information needed
        # for the handler and any hooks invoked by it
        session_controller.signals.initializing.completed.connect(
            pre_sync_transfer_handler
        )
        session_controller.signals.cleanup.completed.connect(post_sync_transfer_handler)
