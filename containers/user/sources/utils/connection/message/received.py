from abc import ABC
from typing import Dict

from ...types import Component
from ...types import Message
from ...types import MessageSubSubType
from ...types import MessageSubType
from ...types import MessageType


class MessageReceived(Message, ABC):

    def __init__(self,
                 messageType,
                 messageSubType,
                 messageSubSubType,
                 data,
                 source: Component,
                 receivedAtLocalTimestamp: float = .0,
                 sentAtSourceTimestamp: float = .0):
        super().__init__(
            messageType=messageType,
            messageSubType=messageSubType,
            messageSubSubType=messageSubSubType,
            data=data,
            receivedAtLocalTimestamp=receivedAtLocalTimestamp,
            sentAtSourceTimestamp=sentAtSourceTimestamp)
        self.source = source

    @staticmethod
    def fromDict(messageInDict: Dict):
        source = Component.fromDict(messageInDict['source'])
        messageReceived = MessageReceived(
            messageType=MessageType(messageInDict['type']),
            messageSubType=MessageSubType(messageInDict['subType']),
            messageSubSubType=MessageSubSubType(messageInDict['subSubType']),
            source=source,
            data=messageInDict['data'],
            sentAtSourceTimestamp=messageInDict['sentAtSourceTimestamp'])
        return messageReceived

    def toDict(self):
        inDict = {
            'type': self.type.value,
            'subType': self.subType.value,
            'subSubType': self.subSubType.value,
            'data': self.data,
            'receivedAtLocalTimestamp': self.receivedAtLocalTimestamp,
            'sentAtSourceTimestamp': self.sentAtSourceTimestamp,
            'source': self.source.toDict()}
        return inDict
