from abc import abstractmethod

from kalanfa.plugins.hooks import define_hook
from kalanfa.plugins.hooks import KalanfaHook


@define_hook
class NetworkLocationDiscoveryHook(KalanfaHook):
    """
    A hook to allow plugins to register callbacks for events when discovering Kalanfa instances
    """

    def on_connect(self, network_location):
        """
        Invoked when a network location becomes available on the network
        :param network_location: The `NetworkLocation` model for instance discovered and verified
        :type network_location: kalanfa.core.discovery.models.NetworkLocation
        """
        pass

    def on_disconnect(self, network_location):
        """
        Invoked when a network location becomes unavailable on the network
        :param network_location: The `NetworkLocation` model for instance no long available
        :type network_location: kalanfa.core.discovery.models.NetworkLocation
        """
        pass


@define_hook
class NetworkLocationBroadcastHook(KalanfaHook):
    @abstractmethod
    def on_renew(self, instance, network_locations):
        """
        Invoked when the current device's broadcast is renewed
        (i.e. the information in the broadcast changes)

        :param instance: The KalanfaInstance for the current device
        :type instance: kalanfa.core.discovery.utils.network.broadcast.KalanfaInstance
        :param network_locations: The list of NetworkLocation models for
            other accessible Kalanfa instances
        :type network_locations: kalanfa.core.discovery.models.NetworkLocation[]
        """
        pass
