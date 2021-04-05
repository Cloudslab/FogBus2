from .tools.waitMessage import waitMessage
from ..registry.base import Registry
from ..registry.roles import User
from ...component import BasicComponent
from ...connection import HandlerReturn
from ...connection import MessageReceived
from ...types import MessageSubType
from ...types import MessageType


class DataHandler:

    def __init__(
            self,
            basicComponent: BasicComponent,
            registry: Registry, ):
        self.basicComponent = basicComponent
        self.registry = registry

    def handleSensoryData(self, message: MessageReceived) -> HandlerReturn:
        data = message.data
        userID = data['userID']
        if userID not in self.registry.registeredManager.users:
            return

        user: User = self.registry.registeredManager.users[userID]
        data['intermediateData'] = data['sensoryData']
        del data['sensoryData']
        for taskName in user.application.entryTaskNameList:
            taskExecutor = user.taskNameToExecutor[taskName]
            self.basicComponent.sendMessage(
                messageType=MessageType.DATA,
                messageSubType=MessageSubType.INTERMEDIATE_DATA,
                data=data,
                destination=taskExecutor)

    def handleResult(self, message: MessageReceived) -> HandlerReturn:
        source = message.source
        data = message.data
        componentID = source.componentID
        taskExecutor = self.registry.registeredManager.taskExecutors[
            componentID]
        userID = taskExecutor.userID
        if userID not in self.registry.registeredManager.users:
            if taskExecutor.waitTimeout <= 0:
                return
            self.registry.registeredManager.taskExecutors.coolOff(taskExecutor)
            responseMessage = waitMessage(taskExecutor)
            self.basicComponent.sendMessage(messageToSend=responseMessage)
            return
        user = self.registry.registeredManager.users[userID]
        self.basicComponent.sendMessage(
            messageType=MessageType.DATA,
            messageSubType=MessageSubType.FINAL_RESULT,
            data=data,
            destination=user)
        # self.basicComponent.debugLogger.debug(
        #     'Sent result to User: %s', user.nameLogPrinting)
