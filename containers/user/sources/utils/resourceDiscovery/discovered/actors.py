from typing import Tuple

from .base import Discovered
from ...config import ConfigActor
from ...types import ComponentRole

_portRange = ConfigActor.portRange
_actorPortRange: Tuple[int, int] = (_portRange[0], _portRange[1] + 1)


class DiscoveredActors(Discovered):

    def __init__(self, portRange: Tuple[int, int] = _actorPortRange):
        Discovered.__init__(
            self,
            role=ComponentRole.ACTOR,
            portRange=
            portRange)
