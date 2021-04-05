import signal
from abc import ABC
from typing import Tuple

from .communicator import Communicator
from .platformInfo import PlatformInfo
from ..connection import MessageReceived
from ..tools.terminate import terminate
from ..types import Address
from ..types import ComponentRole
from ..types import MessageSubType
from ..types import MessageType


class BasicComponent(Communicator, ABC):

    def __init__(
            self,
            role: ComponentRole,
            addr: Address,
            portRange: Tuple[int, int],
            logLevel: int,
            masterAddr: Address,
            remoteLoggerAddr: Address,
            ignoreSocketError: bool = False):
        Communicator.__init__(
            self,
            role=role,
            addr=addr,
            logLevel=logLevel,
            masterAddr=masterAddr,
            remoteLoggerAddr=remoteLoggerAddr,
            ignoreSocketError=ignoreSocketError,
            portRange=portRange)
        self.handleSignal()
        self.serveEvent.wait()
        self.setName(addr=self.addr)
        self.exitTries: int = 0
        self.maxExitTries: int = 3
        self.platform = PlatformInfo()

    def signalHandler(self, sig, frame):
        # https://stackoverflow.com/questions/1112343
        self.exitTries += 1
        self.debugLogger.info(
            '[*] Exiting ... (%d/%d)', self.exitTries, self.maxExitTries)
        if self.exitTries >= self.maxExitTries:
            terminate()
            return
        if self.role in {ComponentRole.MASTER, ComponentRole.REMOTE_LOGGER}:
            terminate()
            return
        data = {'reason': 'Manually interrupted.'}
        self.sendMessage(
            messageType=MessageType.TERMINATION,
            messageSubType=MessageSubType.EXIT,
            data=data,
            destination=self.master)

    def handleSignal(self):
        signal.signal(signal.SIGINT, self.signalHandler)
        signal.signal(signal.SIGTERM, self.signalHandler)

    def handleStop(self, message: MessageReceived):
        self.debugLogger.warning(
            '%s asks me to stop. Reason: %s',
            message.source.nameLogPrinting,
            message.data['reason'])
        self.debugLogger.info('Exit.')
        terminate()

    def uploadMedianReceivedPacketSize(self):
        allSizes = self.receivedPacketSize.calculateAll()
        data = {'sizes': allSizes}
        if not len(allSizes):
            return
        self.sendMessage(
            messageType=MessageType.LOG,
            messageSubType=MessageSubType.MEDIAN_RECEIVED_PACKET_SIZE,
            data=data,
            destination=self.remoteLogger)

    def uploadDelays(self):
        allDelays = self.delays.calculateAll()
        data = {'delays': allDelays}
        if not len(allDelays):
            return
        self.sendMessage(
            messageType=MessageType.LOG,
            messageSubType=MessageSubType.DELAYS,
            data=data,
            destination=self.remoteLogger)
