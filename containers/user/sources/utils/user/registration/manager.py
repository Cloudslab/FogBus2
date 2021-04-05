from time import sleep
from time import time

from ...component import BasicComponent
from ...types import Address
from ...types import Component
from ...types import ComponentRole
from ...types import MessageSubType
from ...types import MessageType


class RegistrationManager:

    def __init__(
            self,
            basicComponent: BasicComponent,
            appName: str,
            label: str):

        self.label = label
        self.appName = appName
        self.basicComponent = basicComponent
        self.actorsCount = 0
        self.requestSentTime = 0

    def registerAt(self, masterAddr: Address):
        self.basicComponent.master = Component(
            hostID='HostID',
            role=ComponentRole.MASTER,
            addr=masterAddr)
        self.waitForActors(masterAddr)
        data = {
            'label': self.label,
            'applicationName': self.appName,
            'hostID': self.basicComponent.hostID}

        self.basicComponent.sendMessage(
            messageType=MessageType.REGISTRATION,
            messageSubType=MessageSubType.REGISTER,
            data=data,
            destination=self.basicComponent.master)
        self.requestSentTime = time() * 1000
        self.basicComponent.debugLogger.info(
            'Sent registration to  %s ...' %
            str(self.basicComponent.master.addr))
        self.basicComponent.isRegistered.wait()

    def waitForActors(self, masterAddr: Address):
        self.actorsCount = 0
        targetCount = 1
        count = 3000

        self.basicComponent.debugLogger.info(
            'Waiting for enough %s at %s [%d/%d]',
            ComponentRole.ACTOR.value,
            str(masterAddr),
            self.actorsCount, targetCount)
        while count > 0:
            self.basicComponent.sendMessage(
                messageType=MessageType.EXPERIMENTAL,
                messageSubType=MessageSubType.ACTORS_COUNT,
                data={},
                destination=self.basicComponent.master)
            sleep(2)
            count -= 1
            if self.actorsCount >= targetCount:
                break

        self.basicComponent.debugLogger.info(
            'There are enough %s at %s [%d/%d]',
            ComponentRole.ACTOR.value,
            str(masterAddr),
            self.actorsCount, targetCount)
        return

    def testConnectivity(self, addr: Address):
        try:
            destination = Component(
                addr=addr)
            self.basicComponent.sendMessage(
                messageType=MessageType.NONE,
                messageSubType=MessageSubType.RESPONSE_TIME,
                data={},
                destination=destination)
            return True
        except Exception:
            return False
