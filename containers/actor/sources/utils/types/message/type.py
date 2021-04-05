from enum import Enum
from enum import unique


@unique
class MessageType(Enum):
    NONE = ''
    EXPERIMENTAL = 'experimental'
    ACKNOWLEDGEMENT = 'acknowledgement'
    DATA = 'data'
    LOG = 'log'
    PLACEMENT = 'placement'
    PROFILING = 'profiling'
    REGISTRATION = 'registration'
    RESOURCE_DISCOVERY = 'resourceDiscovery'
    SCALING = 'scaling'
    TERMINATION = 'termination'
