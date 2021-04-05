from abc import ABC
from typing import Dict

from ...types import Component
from ...types import Message
from ...types import MessageSubSubType
from ...types import MessageSubType
from ...types import MessageType


class MessageToSend(Message, ABC):

    def __init__(
            self,
            messageType: MessageType,
            data: Dict,
            destination: Component,
            messageSubType: MessageSubType = MessageSubType.NONE,
            messageSubSubType: MessageSubSubType = MessageSubSubType.NONE):
        Message.__init__(
            self,
            messageType=messageType,
            messageSubType=messageSubType,
            messageSubSubType=messageSubSubType,
            data=data)
        self.destination = destination

    @staticmethod
    def fromDict(messageInDict: Dict):
        destination = Component.fromDict(
            messageInDict['destination'])
        message = MessageToSend(
            messageType=MessageType(messageInDict['type']),
            messageSubType=MessageSubType(messageInDict['subType']),
            destination=destination,
            messageSubSubType=MessageSubSubType(messageInDict['subSubType']),
            data=messageInDict['data'])
        return message

    def toDict(self):
        inDict = {
            'type': self.type.value,
            'subType': self.subType.value,
            'subSubType': self.subSubType.value,
            'data': self.data,
            'receivedAtLocalTimestamp': self.receivedAtLocalTimestamp,
            'sentAtSourceTimestamp': self.sentAtSourceTimestamp,
            'destination': self.destination.toDict()}
        return inDict
