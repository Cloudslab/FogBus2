from time import sleep
from time import time

from ..registration.manager import RegistrationManager
from ..tasks.base import BaseTask
from ...component import BasicComponent
from ...connection.message.received import MessageReceived
from ...container.manager import ContainerManager
from ...types import Component
from ...types import ComponentRole
from ...types import MessageSubType
from ...types import MessageType


class TaskExecutorMessageHandler:
    def __init__(
            self,
            containerManager: ContainerManager,
            basicComponent: BasicComponent,
            task: BaseTask,
            registrationManager: RegistrationManager):

        self.task = task
        self.registrationManager = registrationManager
        self.containerManager = containerManager
        self.basicComponent = basicComponent
        self.basicComponent.handleMessage = self.handleMessage

    def handleMessage(self, message: MessageReceived):
        if message.typeIs(
                messageType=MessageType.REGISTRATION,
                messageSubType=MessageSubType.REGISTERED):
            self.handleRegistered(message)
        elif message.typeIs(
                messageType=MessageType.PLACEMENT,
                messageSubType=MessageSubType.LOOKUP):
            self.handleTaskExecutorInfo(message)
        elif message.typeIs(
                messageType=MessageType.DATA,
                messageSubType=MessageSubType.INTERMEDIATE_DATA):
            self.handleData(message)
        elif message.typeIs(
                messageType=MessageType.ACKNOWLEDGEMENT,
                messageSubType=MessageSubType.WAIT):
            self.handleWait(message)
        elif message.typeIs(
                messageType=MessageType.PLACEMENT,
                messageSubType=MessageSubType.REUSE):
            self.reRegister(message)

    def handleRegistered(self, message: MessageReceived):
        source = message.source
        self.basicComponent.master = source
        data = message.data
        componentID = data['taskExecutorID']
        hostID = data['actorHostID']
        name = data['name']
        nameConsistent = data['nameConsistent']
        nameLogPrinting = data['nameLogPrinting']
        self.basicComponent.setName(
            addr=self.basicComponent.addr,
            name=name,
            nameConsistent=nameConsistent,
            nameLogPrinting=nameLogPrinting,
            componentID=componentID,
            hostID=hostID)
        self.containerManager.tryRenamingContainerName(newName=nameLogPrinting)
        self.task.medianProcessingTime.taskExecutorName = \
            self.basicComponent.name
        self.registrationManager.lookupChildren()
        self.basicComponent.isRegistered.set()

    def handleTaskExecutorInfo(self, message: MessageReceived):
        data = message.data
        addr = data['taskExecutorAddr']
        taskExecutorAddr = addr[0], addr[1]
        taskToken = data['taskToken']
        if taskToken not in self.registrationManager.childrenTaskTokens:
            return

        self.registrationManager.childrenAddresses[taskToken] = taskExecutorAddr
        childrenCount = len(self.registrationManager.childrenTaskTokens)
        gotCount = len(self.registrationManager.childrenAddresses.keys())
        if childrenCount != gotCount:
            return

    def handleData(self, message: MessageReceived):

        data = message.data
        intermediateData = data['intermediateData']
        result = self.task.exec(intermediateData)
        processingTime = time() * 1000 - message.receivedAtLocalTimestamp
        self.task.updateProcessingTime(processingTime)
        if result is None:
            return
        # print(self.task.taskName, self.registrationManager.childrenAddresses)
        if len(self.registrationManager.childrenAddresses.keys()):
            data['intermediateData'] = result
            for addr in self.registrationManager.childrenAddresses.values():
                child = Component(addr=addr)
                self.basicComponent.sendMessage(
                    messageType=MessageType.DATA,
                    messageSubType=MessageSubType.INTERMEDIATE_DATA,
                    data=data,
                    destination=child)
            return
        del data['intermediateData']
        data['finalResult'] = result
        self.basicComponent.sendMessage(
            messageType=MessageType.DATA,
            messageSubType=MessageSubType.FINAL_RESULT,
            data=data,
            destination=self.basicComponent.master)
        return

    def handleWait(self, message: MessageReceived):
        self.basicComponent.isRegistered.clear()
        self.basicComponent.sendMessage(
            messageType=MessageType.ACKNOWLEDGEMENT,
            messageSubType=MessageSubType.WAITING,
            data={},
            destination=self.basicComponent.master)
        waitTimeout = message.data['waitTimeout']
        while True:
            sleep(1)
            waitTimeout -= 1
            if self.basicComponent.isRegistered.isSet():
                break
            if waitTimeout <= 0:
                break
        if self.basicComponent.isRegistered.isSet():
            return
        # TODO: solve problem: because of transaction time, it is possible
        #  that the following code terminates taskExecutor during the time that
        #  master asks it to reRegister

        data = {
            'reason': 'Be idle more than %s seconds' % waitTimeout}
        self.basicComponent.sendMessage(
            messageType=MessageType.TERMINATION,
            messageSubType=MessageSubType.EXIT,
            data=data,
            destination=self.basicComponent.master)

    def reRegister(self, message: MessageReceived):
        data = message.data
        userID = data['userID']
        taskName = data['taskName']
        taskToken = data['taskToken']
        childrenTaskTokens = data['childrenTaskTokens']
        self.registrationManager.setCredentials(
            userID=userID,
            taskName=taskName,
            taskToken=taskToken,
            childrenTaskTokens=childrenTaskTokens)
        self.registrationManager.registerAt(
            userID=userID,
            taskName=taskName,
            taskToken=taskToken,
            masterAddr=self.basicComponent.master.addr,
            isReRegister=True)
        self.basicComponent.debugLogger.info(
            'Re-registering for %s-%s', ComponentRole.USER.value, userID)
