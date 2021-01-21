import socket
import struct
import threading
import traceback
import pickle
from queue import Queue
from typing import Any, Dict, Tuple
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


class Source:

    def __init__(
            self,
            addr,
            role,
            id_,
    ):
        self.addr = addr
        self.role = role
        self.id = id_


class Connection:
    def __init__(self, addr: Tuple[str, int]):
        self.addr: Tuple[str, int] = addr

    def __send(self, message: bytes, retries: int = 3):
        if not retries:
            raise OSError
        try:
            clientSocket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM)
            clientSocket.connect(self.addr)
            package = struct.pack(">L", len(message)) + message
            clientSocket.sendall(package)
            clientSocket.close()
        except OSError:
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
            messagesQueue: Queue[Message],
            threadNumber: int = 1):
        self.addr = addr
        self.messageQueue: Queue[Message] = messagesQueue
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
            message = self.__receiveMessage(request.clientSocket)
            self.messageQueue.put(Message(content=message))

    @staticmethod
    def __receiveMessage(clientSocket: socket.socket) -> Dict:
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
        result = decrypt(result)
        return result


if __name__ == '__main__':
    serverIP = ''
    serverPort = 5000
    addr_ = ('', 5000)
    server_ = Server(addr_, Queue())
    server_.run()
    Connection(addr_).send({})
