from ..registry.base import Registry
from ...connection import HandlerReturn
from ...connection import MessageReceived
from ...connection import MessageToSend
from ...types import MessageSubType
from ...types import MessageType


class ExperimentalHandler:

    def __init__(self, registry: Registry):
        self.registry = registry

    def handleActorsCount(self, message: MessageReceived) -> HandlerReturn:
        source = message.source
        data = {'actorsCount': len(self.registry.registeredManager.actors)}
        messageToSend = MessageToSend(
            messageType=MessageType.EXPERIMENTAL,
            messageSubType=MessageSubType.ACTORS_COUNT,
            data=data,
            destination=source)
        return messageToSend
