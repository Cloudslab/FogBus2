from ..registry.base import Registry
from ...connection import MessageReceived
from ...types import MessageSubType
from ...types import MessageType


class PlacementHandler:
    def __init__(self, registry: Registry):
        self.registry = registry

    def handleLookup(self, message: MessageReceived):
        source = message.source
        data = message.data
        taskToken = data['taskToken']
        if taskToken not in self.registry.registeredManager.taskExecutors:
            return
        taskExecutor = self.registry.registeredManager.taskExecutors[taskToken]
        data = {
            'taskExecutorAddr': list(taskExecutor.addr),
            'taskToken': taskExecutor.task.token}
        self.registry.basicComponent.sendMessage(
            messageType=MessageType.PLACEMENT,
            messageSubType=MessageSubType.LOOKUP,
            data=data,
            destination=source)
        return
