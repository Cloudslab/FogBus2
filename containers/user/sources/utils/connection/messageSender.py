import struct
from pprint import pformat
from queue import Queue
from socket import AF_INET
from socket import SOCK_STREAM
from socket import socket
from time import sleep
from time import time
from traceback import print_exc as printExc
from typing import Dict
from typing import Tuple

from .message import MessageToSend
from ..debugLogPrinter import DebugLogPrinter
from ..tools import encrypt
from ..tools import terminate
from ..types import Address
from ..types import Component
from ..types import ComponentRole
from ..types import MessageSubSubType
from ..types import MessageSubType
from ..types import MessageType

FORMAT = '>L'


class MessageSender(Component, DebugLogPrinter):

    def __init__(
            self,
            role: ComponentRole,
            addr: Address,
            logLevel: int,
            ignoreSocketError: bool = False):
        DebugLogPrinter.__init__(self, logLevel)
        Component.__init__(self, role=role, addr=addr)
        self.messagesToSendQueue: Queue[
            Tuple[MessageToSend, bool, bool]] = Queue()
        self.ignoreSocketError = ignoreSocketError

    def sendBytes(
            self,
            messageInBytes: bytes,
            destAddr: Address,
            retries: int = 5):
        clientSocket = socket(AF_INET, SOCK_STREAM)
        try:
            clientSocket.settimeout(10)
            clientSocket.connect(destAddr)
            package = struct.pack(FORMAT, len(messageInBytes)) + messageInBytes
            clientSocket.sendall(package)
            clientSocket.close()
        except OSError:
            clientSocket.close()
            if retries > 0:
                self.resendBytes(messageInBytes, destAddr, retries - 1)
                return
            raise OSError
        except ConnectionRefusedError:
            clientSocket.close()
            sleep(3)
            if retries > 0:
                self.resendBytes(messageInBytes, destAddr, retries - 1)
                return
            raise ConnectionRefusedError

    def resendBytes(self, message: bytes, destination: Address, retries: int):
        sleep(0.1)
        self.sendBytes(messageInBytes=message,
                       destAddr=destination,
                       retries=retries - 1)

    def sendMessage(
            self,
            messageToSend: MessageToSend = None,
            data: Dict = None,
            destination: Component = None,
            messageType: MessageType = MessageType.NONE,
            messageSubType: MessageSubType = MessageSubType.NONE,
            messageSubSubType: MessageSubSubType = MessageSubSubType.NONE,
            ignoreSocketError: bool = None,
            showFailure: bool = True):

        if messageToSend is None:
            messageToSend = MessageToSend(
                messageType=messageType,
                data=data,
                destination=destination,
                messageSubType=messageSubType,
                messageSubSubType=messageSubSubType)
        messageToSend.sentAtSourceTimestamp = time() * 1000

        destination = messageToSend.destination
        component = Component.fromDict(destination.toDict())
        messageToSend.destination = component

        self.messagesToSendQueue.put(
            (messageToSend, ignoreSocketError, showFailure))

    def messageSender(self, retries: int = 10):
        while True:
            messageToSend, ignoreSocketError, showFailure = self.messagesToSendQueue.get()
            messageInDict = messageToSend.toDict()
            messageInDict['source'] = self.toDict()
            try:
                messageInBytes = encrypt(messageInDict)
                self.sendBytes(
                    messageInBytes=messageInBytes,
                    destAddr=messageToSend.destination.addr,
                    retries=retries)
            except (ConnectionRefusedError, OSError):
                if ignoreSocketError is None:
                    ignoreSocketError = self.ignoreSocketError
                if not ignoreSocketError:
                    printExc()
                if showFailure:
                    self.debugLogger.debug(
                        'Failed to send message: %s \n %s',
                        messageToSend.destination.nameLogPrinting,
                        pformat(messageInDict))
                sleep(1)
                self.messagesToSendQueue.put(
                    (messageToSend, ignoreSocketError, showFailure))
                if ignoreSocketError:
                    continue
                terminate()
