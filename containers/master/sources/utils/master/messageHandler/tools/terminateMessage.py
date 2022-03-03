from typing import Dict

from ....connection import MessageToSend
from ....types import Component
from ....types import MessageSubType
from ....types import MessageType


def terminateMessage(
        component: Component, reason: str = 'No Reason', data: Dict = None) -> \
        MessageToSend:
    if data is None:
        data = {}
    data['reason'] = reason
    if 'packetSize' not in data:
        data['packetSize'] = 0
    messageToSend = MessageToSend(
        messageType=MessageType.TERMINATION,
        messageSubType=MessageSubType.STOP,
        data=data,
        destination=component)
    return messageToSend
