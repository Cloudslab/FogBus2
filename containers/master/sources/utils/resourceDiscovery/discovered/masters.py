from typing import Tuple

from .base import Discovered
from ...config import ConfigMaster
from ...types import ComponentRole

_portRange = ConfigMaster.portRange
_masterPortRange: Tuple[int, int] = (_portRange[0], _portRange[1] + 1)


class DiscoveredMasters(Discovered):

    def __init__(self, portRange: Tuple[int, int] = _masterPortRange):
        Discovered.__init__(
            self,
            role=ComponentRole.MASTER,
            portRange=
            portRange)
