from abc import ABC
from pprint import pformat
from time import time
from traceback import print_exc
from typing import Tuple

from .message import MessageReceived
from .messageReceiver import MessageReceiver
from ..tools.terminate import terminate
from ..types import Address
from ..types import ComponentRole
from ..types import MessageSubSubType
from ..types import MessageSubType
from ..types import MessageType
from ..types import PairsMedian
from ..types import SequenceMedian
from ..types import SynchronizedAttribute


class BasicMessageHandler(MessageReceiver, ABC):

    def __init__(
            self,
            role: ComponentRole,
            addr: Address,
            logLevel: int,
            portRange: Tuple[int, int],
            ignoreSocketError: bool = False):
        MessageReceiver.__init__(
            self,
            role=role,
            addr=addr,
            logLevel=logLevel,
            ignoreSocketError=ignoreSocketError,
            portRange=portRange)
        self.receivedPacketSize: PairsMedian[
            str, SequenceMedian] = PairsMedian()
        self.delays: PairsMedian[str, SequenceMedian] = PairsMedian()
        self.lastTimeTestDiff = .0
        self.testDiffInterval = 10

    def handle(self):
        while True:
            try:
                message, packetSize = self.messagesReceivedQueue.get()
                message.receivedAtLocalTimestamp = time() * 1000
                if message.typeIs(MessageType.PROFILING,
                                  MessageSubType.TIME_DIFFERENCE):
                    self.handleTimeDiff(message)
                    continue
                elif message.typeIs(messageType=MessageType.TERMINATION):
                    if self.role is not ComponentRole.MASTER:
                        self.handleTermination(message)
                        continue
                elif message.typeIs(
                        messageType=MessageType.RESOURCE_DISCOVERY,
                        messageSubType=MessageSubType.PROBE,
                        messageSubSubType=MessageSubSubType.TRY):
                    self.handleProbeTry(message)
                    continue
                else:
                    self.testTimeDiff(message)
                self.handlePacketSize(message, packetSize)
                self.handleMessage(message)
            except Exception:
                print_exc()
                self.debugLogger.warning('Exception above has been ignored')

    def handleProbeTry(self, message: MessageReceived):
        data = message.data
        targetRole = data['targetRole']
        if not targetRole == self.role.value:
            return
        data = {'role': self.role.value}
        self.sendMessage(
            messageType=MessageType.RESOURCE_DISCOVERY,
            messageSubType=MessageSubType.PROBE,
            messageSubSubType=MessageSubSubType.RESULT,
            data=data,
            destination=message.source)
        return

    def handleTermination(self, message: MessageReceived):
        if self.role in {ComponentRole.REMOTE_LOGGER, ComponentRole.MASTER}:
            return
        if not message.typeIs(messageSubType=MessageSubType.STOP):
            return
        if self.role == ComponentRole.USER:
            self.handleMessage(message=message)
            return
        data = message.data
        self.debugLogger.warning('Exiting: %s', data['reason'])
        terminate()

    def handlePacketSize(
            self, message: MessageReceived,
            packetSize: int):

        self._handlePacketSize(
            self, message, packetSize, attributeName='receivedPacketSize')

    @SynchronizedAttribute
    def _handlePacketSize(
            self, message: MessageReceived,
            packetSize: int,
            attributeName='receivedPacketSize'):
        nameConsistent = message.source.nameConsistent
        self.receivedPacketSize[nameConsistent].update(packetSize)

    def handleTimeDiff(self, message: MessageReceived):
        self._handleTimeDiff(self, message=message, attributeName='delays')

    @SynchronizedAttribute
    def _handleTimeDiff(
            self,
            message: MessageReceived,
            attributeName='delays'):
        data = message.data
        A = data['A']
        X = data['X']
        Y = message.sentAtSourceTimestamp
        B = message.receivedAtLocalTimestamp
        # delay = (B - A - Y + X) / 2
        delayAtMost = B - A - Y + X
        self.delays[message.source.nameConsistent].update(delayAtMost)

    def testTimeDiff(self, receivedMessage: MessageReceived):
        currentTime = time()
        if currentTime - self.lastTimeTestDiff < self.testDiffInterval:
            return
        data = {
            'A': receivedMessage.sentAtSourceTimestamp,
            'X': receivedMessage.receivedAtLocalTimestamp}
        self.sendMessage(
            messageType=MessageType.PROFILING,
            messageSubType=MessageSubType.TIME_DIFFERENCE,
            data=data,
            destination=receivedMessage.source)
        self.lastTimeTestDiff = currentTime

    def handleMessage(self, message: MessageReceived):
        # This method should be overridden by messageHandler of components
        # For example, ActorMessageHandler should have the following code
        #     self.basicComponent.handleMessage = self.handleMessage
        if message.source.addr == self.addr:
            return
        self.debugLogger.warning(
            'Received message but component is not ready yet: \n %s',
            pformat(message.toDict()))
