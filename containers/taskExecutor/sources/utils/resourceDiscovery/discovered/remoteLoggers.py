from typing import Tuple

from .base import Discovered
from ...config import ConfigRemoteLogger
from ...types import ComponentRole

_portRange = ConfigRemoteLogger.portRange
_remoteLoggerPortRange: Tuple[int, int] = (_portRange[0], _portRange[1])


class DiscoveredRemoteLoggers(Discovered):

    def __init__(self, portRange: Tuple[int, int] = _remoteLoggerPortRange):
        Discovered.__init__(
            self,
            role=ComponentRole.REMOTE_LOGGER,
            portRange=
            portRange)
