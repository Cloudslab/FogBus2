from abc import abstractmethod
from queue import Queue
from socket import AF_INET
from socket import error
from socket import SO_REUSEADDR
from socket import SOCK_STREAM
from socket import socket
from socket import SOL_SOCKET
from struct import calcsize
from struct import unpack
from threading import Event
from threading import Thread
from traceback import print_exc
from typing import Any
from typing import Tuple

from .message import MessageReceived
from .messageSender import FORMAT
from .messageSender import MessageSender
from .request import ConnectionRequest
from ..tools import decrypt
from ..tools.terminate import terminate
from ..types import Address
from ..types import ComponentRole

PAYLOAD_SIZE = calcsize(FORMAT)


class MessageReceiver(MessageSender):

    def __init__(
            self,
            role: ComponentRole,
            addr: Address,
            portRange: Tuple[int, int],
            logLevel: int,
            ignoreSocketError: bool = False,
            messagesReceivedQueue: Queue[
                Tuple[MessageReceived, int]] = Queue(),
            threadNumber: int = 8):
        MessageSender.__init__(
            self,
            role=role,
            addr=addr,
            logLevel=logLevel,
            ignoreSocketError=ignoreSocketError)
        self.portRange = portRange
        self.serverSocket = socket(
            AF_INET,
            SOCK_STREAM)
        self.messagesReceivedQueue: Queue[
            Tuple[MessageReceived, int]] = messagesReceivedQueue
        self.threadsNumber: int = threadNumber
        self.requests: Queue[ConnectionRequest] = Queue()
        self.serveEvent: Event = Event()
        self.autoListen()
        self.prepareThreadsPool()

    def prepareThreadsPool(self):
        for i in range(self.threadsNumber):
            Thread(
                target=self.messageReceiver,
                name="MessageReceiver-%d" % i).start()
            Thread(
                target=self.messageSender,
                name="MessageSender-%d" % i).start()
            for _ in range(2):
                Thread(
                    target=self.handle,
                    name="BasicMessageHandler-%d" % i).start()
        Thread(target=self.serve, name="ConnectionServer").start()

    def autoListen(self):

        listenSuccess = self.tryListeningOn(
            addr=self.addr, portRange=self.portRange)
        if not listenSuccess:
            print_exc()
            self.debugLogger.error(
                'Failed to listen on addr: %s [%d, %d)',
                str(self.addr), self.portRange[0], self.portRange[1])
            terminate()

    def serve(self):

        self.serveEvent.set()
        while True:
            clientSocket, clientAddress = self.serverSocket.accept()
            request = ConnectionRequest(clientSocket, clientAddress)
            self.requests.put(request)

    def tryListeningOn(self, addr: Address, portRange: Tuple[int, int]) -> bool:
        ip, targetPort = addr[0], addr[1]
        portLower, portUpper = portRange
        if targetPort != 0 and \
                (targetPort < portLower or targetPort >= portUpper):
            raise Exception('Port %s is out of config [%d, %d)' % (
                targetPort, portLower, portUpper))
        # Specified port
        if targetPort != 0:
            success = self.listenOn(addr=(ip, targetPort))
            if success:
                return True
            else:
                return False
        # Did not specify port
        for targetPort in range(portRange[0], portRange[1]):
            success = self.listenOn(addr=(ip, targetPort))
            if success:
                return True
        return False

    def listenOn(self, addr: Address) -> bool:
        try:
            self.serverSocket.setsockopt(
                SOL_SOCKET,
                SO_REUSEADDR,
                1)
            self.serverSocket.bind(addr)
            self.serverSocket.listen()
            self.addr = self.serverSocket.getsockname()
            self.debugLogger.info(
                'Listening at %s' % str(self.addr))
            return True
        except OSError:
            return False

    def messageReceiver(self):
        while True:
            try:
                request = self.requests.get()
                content, packetSize = self.receiveMessage(request.clientSocket)
                if packetSize == 0:
                    continue
                message = MessageReceived.fromDict(content)
                self.messagesReceivedQueue.put((message, packetSize))
            except OSError:
                continue

    @staticmethod
    def receiveMessage(clientSocket: socket) -> Tuple[Any, int]:
        result = None
        buffer = b''
        try:
            clientSocket.settimeout(3)
            while len(buffer) < PAYLOAD_SIZE:
                buffer += clientSocket.recv(4096)
            packedDataSize = buffer[:PAYLOAD_SIZE]
            buffer = buffer[PAYLOAD_SIZE:]
            dataSize = unpack(FORMAT, packedDataSize)[0]
            while len(buffer) < dataSize:
                buffer += clientSocket.recv(4096)
            data = buffer[:dataSize]
            result = data
        except (OSError, error):
            pass
        clientSocket.close()
        if result is None:
            return {}, 0
        return decrypt(result), len(result)

    @abstractmethod
    def handle(self):
        pass

    @abstractmethod
    def handlerMessage(self):
        pass
