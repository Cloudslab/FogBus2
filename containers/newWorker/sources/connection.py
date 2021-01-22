import socket
import struct
import threading
import traceback
import pickle
import os
from queue import Queue
from typing import Any, Dict, Tuple, List
from exceptions import *


def encrypt(obj) -> bytes:
    data = pickle.dumps(obj, 0)
    return data


def decrypt(msg: bytes) -> Dict:
    try:
        obj = pickle.loads(msg, fix_imports=True, encoding="bytes")
        return obj
    except Exception:
        traceback.print_exc()


class Identity:
    def __init__(
            self,
            role: str,
            id_: int,
            name: str
    ):
        self.role: str = role
        self.id: int = id_
        self.name: str = name


class Source(Identity):

    def __init__(
            self,
            role: str,
            id_: int,
            name: str,
            addr: Tuple[str, int]):
        super().__init__(role, id_, name)
        self.addr: Tuple[str, int] = addr


class RoundTripDelay(Identity):

    def __init__(
            self,
            role: str,
            id_: int,
            name: str,
            delay: float):
        super().__init__(role, id_, name)
        self.delay: float = delay * 1000

    def update(self, delay: float):
        self.delay = (self.delay + delay * 1000) / 2


class ReceivedPackageSize(Identity):

    def __init__(
            self,
            role: str,
            id_: int,
            name: str):
        super().__init__(role, id_, name)
        self.__maxRecordNumber = 100
        self.__receivedIndex = 0
        self.__received: List[int] = [0 for _ in range(self.__maxRecordNumber)]

    def received(self, bytes_: int):
        self.__received[self.__receivedIndex] = bytes_
        self.__receivedIndex = (self.__receivedIndex + 1) % self.__maxRecordNumber

    def average(self):
        total = 0
        count = 0
        for received in self.__received:
            if received == 0:
                break
            total += received
            count += 1

        if count == 0:
            return 0
        return total / count

    def __str__(self):
        return str(self.average())


class Connection:
    def __init__(self, addr):
        self.addr = addr

    def __send(self, message: bytes, retries: int = 3):
        if not retries:
            traceback.print_exc()
            os._exit(-1)
        clientSocket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM)
        try:
            clientSocket.connect(self.addr)
            package = struct.pack(">L", len(message)) + message
            clientSocket.sendall(package)
            clientSocket.close()
        except (OSError, ConnectionRefusedError):
            clientSocket.close()
            self.__send(message=message, retries=retries - 1)

    def send(self, message: Dict, retries: int = 3):
        self.__send(encrypt(message), retries=retries)


class Request:

    def __init__(self, clientSocket: socket.socket, clientAddr):
        self.clientSocket: clientSocket = clientSocket
        self.clientAddr = clientAddr


class Message:
    def __init__(self, content: Dict):
        self.content: Dict = content

        if 'source' not in self.content:
            raise MessageDoesNotContainSourceInfo

        if 'type' not in self.content:
            raise MessageDoesNotContainType

        self.type = self.content['type']
        self.source: Source = self.content['source']


class Server:

    def __init__(
            self,
            addr,
            messagesQueue: Queue[Tuple[Message, int]],
            threadNumber: int = 20):
        self.addr = addr
        self.messageQueue: Queue[Tuple[Message, int]] = messagesQueue

        self.threadNumber: int = threadNumber
        self.requests: Queue[Request] = Queue()
        self.run()

    def run(self):
        for i in range(self.threadNumber):
            t = threading.Thread(
                target=self.__handleThread,
                name="HandlingThread-%d" % i
            )
            t.start()
        server = threading.Thread(
            target=self.__serve,
            name="Server"
        )
        server.start()

    def __serve(self):
        serverSocket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM)
        serverSocket.bind(self.addr)
        serverSocket.listen()
        while True:
            clientSocket, clientAddress = serverSocket.accept()
            request = Request(clientSocket, clientAddress)
            self.requests.put(request)

    def __handleThread(self):
        while True:
            request = self.requests.get()
            message, messageSize = self.__receiveMessage(request.clientSocket)
            self.messageQueue.put(
                (Message(content=message), messageSize))

    @staticmethod
    def __receiveMessage(clientSocket: socket.socket) -> Tuple[Dict, int]:
        result = None
        buffer = b''
        payloadSize = struct.calcsize('>L')

        try:
            while len(buffer) < payloadSize:
                buffer += clientSocket.recv(4096)

            packedDataSize = buffer[:payloadSize]
            buffer = buffer[payloadSize:]
            dataSize = struct.unpack('>L', packedDataSize)[0]

            while len(buffer) < dataSize:
                buffer += clientSocket.recv(4096)

            data = buffer[:dataSize]
            result = data

        except OSError:
            traceback.print_exc()

        clientSocket.close()
        if result is None:
            return {}, 0
        return decrypt(result), len(result)


if __name__ == '__main__':
    serverIP = ''
    serverPort = 5000
    addr_ = ('', 5000)
    server_ = Server(addr_, Queue())
    server_.run()
    Connection(addr_).send({})
