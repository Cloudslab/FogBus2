from .actors import DiscoveredActors
from .masters import DiscoveredMasters
from .remoteLoggers import DiscoveredRemoteLoggers


class DiscoveredManager:
    actors: DiscoveredActors = DiscoveredActors()
    masters: DiscoveredMasters = DiscoveredMasters()
    remoteLoggers: DiscoveredRemoteLoggers = DiscoveredRemoteLoggers()
