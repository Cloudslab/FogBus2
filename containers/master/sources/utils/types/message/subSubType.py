from enum import Enum
from enum import unique


@unique
class MessageSubSubType(Enum):
    NONE = ''
    DEFAULT = 'default'
    EXPERIMENTAL = 'experimental'
    RECEIVE = 'receive'
    SEND = 'send'
    RESULT = 'result'
    TRY = 'try'
