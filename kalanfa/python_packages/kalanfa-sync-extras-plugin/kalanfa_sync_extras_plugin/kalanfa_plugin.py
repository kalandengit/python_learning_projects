from kalanfa.core.auth.hooks import FacilityDataSyncHook
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.plugins.hooks import register_hook


class SyncExtrasPlugin(KalanfaPluginBase):
    kalanfa_options = "options"


@register_hook
class SyncExtrasPluginHook(FacilityDataSyncHook):
    _initialize_operations = None
    _finalize_operations = None

    def get_initialize_operations(self):
        """
        Import and cache the operation here to avoid import ordering issues with dependencies
        :rtype: list[kalanfa_sync_extras_plugin.sync.operations.BackgroundInitializeJobOperation]
        """
        from kalanfa_sync_extras_plugin.sync.operations import (
            BackgroundInitializeJobOperation,
        )

        if self._initialize_operations is None:
            self._initialize_operations = [BackgroundInitializeJobOperation()]
        return self._initialize_operations

    def get_finalize_operations(self):
        """
        Import and cache the operation here to avoid import ordering issues with dependencies
        :rtype: list[kalanfa_sync_extras_plugin.sync.operations.BackgroundFinalizeJobOperation]
        """
        from kalanfa_sync_extras_plugin.sync.operations import (
            BackgroundFinalizeJobOperation,
        )

        if self._finalize_operations is None:
            self._finalize_operations = [BackgroundFinalizeJobOperation()]
        return self._finalize_operations

    serializing_operations = property(get_initialize_operations)
    queuing_operations = property(get_initialize_operations)
    dequeuing_operations = property(get_finalize_operations)
    deserializing_operations = property(get_finalize_operations)
    cleanup_operations = property(get_finalize_operations)
