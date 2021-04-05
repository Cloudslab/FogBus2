from abc import ABC
from typing import Dict

from .subSubType import MessageSubSubType
from .subType import MessageSubType
from .type import MessageType
from ..basic import AutoDictionary
from ..basic import SerializableDictionary


class Message(AutoDictionary, SerializableDictionary, ABC):

    def __init__(
            self,
            messageType: MessageType,
            messageSubType: MessageSubType,
            messageSubSubType: MessageSubSubType = None,
            data: Dict = None,
            receivedAtLocalTimestamp: float = .0,
            sentAtSourceTimestamp: float = .0):

        self.type = messageType
        self.subType = messageSubType
        self.subSubType = messageSubSubType
        self.data = data
        self.receivedAtLocalTimestamp = receivedAtLocalTimestamp
        self.sentAtSourceTimestamp = sentAtSourceTimestamp

    def typeIs(
            self,
            messageType: MessageType = None,
            messageSubType: MessageSubType = None,
            messageSubSubType: MessageSubSubType = None, ) -> bool:
        if messageType is not None:
            if self.type is not messageType:
                return False
        if messageSubType is not None:
            if self.subType is not messageSubType:
                return False
        if messageSubSubType is not None:
            if self.subSubType is not messageSubSubType:
                return False
        return True
