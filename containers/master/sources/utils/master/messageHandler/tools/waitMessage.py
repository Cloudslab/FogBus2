from ...registry.roles.taskExecutor import TaskExecutor

from ....connection import MessageToSend
from ....types import MessageSubType
from ....types import MessageType


def waitMessage(taskExecutor: TaskExecutor) -> MessageToSend:
    messageToSend = MessageToSend(
        messageType=MessageType.ACKNOWLEDGEMENT,
        messageSubType=MessageSubType.WAIT,
        data={'waitTimeout': taskExecutor.waitTimeout},
        destination=taskExecutor)
    return messageToSend
