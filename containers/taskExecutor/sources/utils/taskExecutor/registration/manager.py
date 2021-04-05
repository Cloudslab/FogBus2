from time import sleep
from typing import Dict
from typing import List

from ...component import BasicComponent
from ...types import Address
from ...types import Component
from ...types import ComponentRole
from ...types import MessageSubType
from ...types import MessageType


class RegistrationManager:

    def __init__(
            self,
            userID: str,
            actorID: str,
            taskName: str,
            taskToken: str,
            childrenTaskTokens: List[str],
            basicComponent: BasicComponent,
            totalCPUCores: int,
            cpuFreq: float):
        self.childrenTaskTokens = childrenTaskTokens
        self.taskToken = taskToken
        self.taskName = taskName
        self.actorID = actorID
        self.userID = userID
        self.basicComponent = basicComponent
        self.childrenAddresses: Dict[str, tuple] = {}
        self.totalCPUCores = totalCPUCores
        self.cpuFreq = cpuFreq

    def setCredentials(
            self,
            userID: str,
            taskName: str,
            taskToken: str,
            childrenTaskTokens: List[str]):
        self.userID = userID
        self.taskName = taskName
        self.taskToken = taskToken
        self.childrenTaskTokens = childrenTaskTokens

    def registerAt(
            self,
            userID: str,
            taskName: str,
            taskToken: str,
            masterAddr: Address,
            isReRegister: bool = False):
        if isReRegister:
            self.basicComponent.isRegistered.clear()
            self.basicComponent.master = Component(
                role=ComponentRole.MASTER,
                addr=masterAddr)
        data = {
            'userID': userID,
            'actorID': self.actorID,
            'taskName': taskName,
            'taskToken': taskToken}
        self.basicComponent.sendMessage(
            messageType=MessageType.REGISTRATION,
            messageSubType=MessageSubType.REGISTER,
            data=data,
            destination=self.basicComponent.master)

    def lookupChildren(self):
        while True:
            childrenCount = len(self.childrenTaskTokens)
            gotCount = len(self.childrenAddresses.keys())
            if childrenCount == gotCount:
                break
            for childTaskToken in self.childrenTaskTokens:
                if childTaskToken in self.childrenAddresses:
                    continue
                data = {'taskToken': childTaskToken}
                self.basicComponent.sendMessage(
                    messageType=MessageType.PLACEMENT,
                    messageSubType=MessageSubType.LOOKUP,
                    data=data,
                    destination=self.basicComponent.master)
            sleep(2)
        data = {'taskToken': self.taskToken}
        self.basicComponent.sendMessage(
            messageType=MessageType.ACKNOWLEDGEMENT,
            messageSubType=MessageSubType.READY,
            data=data,
            destination=self.basicComponent.master)
        self.basicComponent.debugLogger.debug(
            'Got %d children\'s addr' % len(self.childrenTaskTokens))
