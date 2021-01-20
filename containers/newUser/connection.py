import socket
import struct
import threading
import traceback
from queue import Queue
from message import encrypt, decrypt
from typing import Any, Dict
from abc import abstractmethod


class Connection:
    def __init__(self, ip: str, port: int):
        self.ip: str = ip
        self.port: int = port
        self.__payloadSize = struct.calcsize('>L')

    def __send(self, data: bytes, retries: int = 3):
        if not retries:
            raise OSError
        try:
            clientSocket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM)
            clientSocket.connect((self.ip, self.port))
            package = struct.pack(">L", len(data)) + data
            clientSocket.sendall(package)
            clientSocket.close()
        except OSError:
            self.__send(data=data, retries=retries - 1)

    def send(self, data: Any, retries: int = 3):
        encryptData = encrypt(data)
        self.__send(data=encryptData, retries=retries)


class Request:

    def __init__(self, clientSocket: socket.socket, ip: str, port: int):
        self.clientSocket: clientSocket = clientSocket
        self.ip: str = ip
        self.port: int = port


class Server:

    def __init__(
            self,
            ip: str,
            port: int,
            threadNumber: int = 30):
        self.ip: str = ip
        self.port: int = port
        self.threadNumber: int = threadNumber

        self.requests: Queue[Request] = Queue()

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
        serverSocket.bind((self.ip, self.port))
        serverSocket.listen()
        while True:
            clientSocket, clientAddress = serverSocket.accept()
            request = Request(clientSocket, clientAddress[0], clientAddress[1])
            self.requests.put(request)

    def __handleThread(self):
        while True:
            request = self.requests.get()
            message = self.__receiveMessage(request.clientSocket)
            self.handle(message, request.ip, request.port)

    @staticmethod
    def __receiveMessage(clientSocket: socket.socket) -> Dict:
        result = None
        buffer = b''
        payloadSize = struct.calcsize('>L')

        try:
            while len(buffer) < payloadSize:
                buffer = clientSocket.recv(4096)

            packedDataSize = buffer[:payloadSize]
            buffer = buffer[payloadSize:]
            dataSize = struct.unpack('>L', packedDataSize)[0]

            while len(buffer) < dataSize:
                buffer = clientSocket.recv(4096)

            data = buffer[:dataSize]
            result = data

        except OSError:
            traceback.print_exc()

        clientSocket.close()
        if result is not None:
            result = decrypt(result)
        return result

    @abstractmethod
    def handle(self, message: Dict, ip: str, port: int):
        pass


if __name__ == '__main__':
    serverIP = ''
    serverPort = 5000
    server_ = Server(serverIP, serverPort)
    server_.run()
