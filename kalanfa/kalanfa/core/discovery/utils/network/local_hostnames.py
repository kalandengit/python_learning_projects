from kalanfa.core.discovery.tasks import sync_local_hostnames
from kalanfa.core.discovery.utils.network.broadcast import KalanfaInstanceListener


class LocalHostnameListener(KalanfaInstanceListener):
    """
    Persists the `.local` hostnames the broadcast owns to the database, so
    `get_urls()` can read them from any process.
    """

    def update_local_names(self, hostnames):
        sync_local_hostnames.enqueue(args=(hostnames,))
