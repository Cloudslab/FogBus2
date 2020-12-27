import logging
import threading
import struct
import socket
from logger import get_logger
from queue import Queue
from typing import NoReturn


class Client:

    def __init__(self, socket_: socket.socket, sendingQueue: Queue[bytes], receivingQueue: Queue[bytes]):
        self.socket: socket.socket = socket_
        self.sendingQueue: Queue[bytes] = sendingQueue
        self.receivingQueue: Queue[bytes] = receivingQueue
        self.active = True


class DataManager:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.host: str = host
        self.port: int = port
        self.__currentSocketID = 0
        self.__lockSocketID: threading.Lock = threading.Lock()
        self.__sockets: dict[int, Client] = {}
        self.__serverSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = get_logger('Master-MainService', logLevel)

    def run(self):
        threading.Thread(target=self.__serve).start()

    def __newSocketID(self) -> int:
        self.__lockSocketID.acquire()
        self.__currentSocketID += 1
        socketID = self.__currentSocketID
        self.__lockSocketID.release()
        return socketID

    def __serve(self):
        self.__serverSocket.bind((self.host, self.port))
        self.__serverSocket.listen()
        self.logger.info('[*] serves at %s:%d over tcp.', self.host, self.port)
        while True:
            clientSocket, _ = self.__serverSocket.accept()

            receivingQueue: Queue[bytes] = Queue()
            sendingQueue: Queue[bytes] = Queue()
            socketID = self.__newSocketID()
            self.__sockets[socketID] = Client(clientSocket, receivingQueue, sendingQueue)
            threading.Thread(target=self.__receiveData,
                             args=(clientSocket, receivingQueue
                                   )).start()
            threading.Thread(target=self.__sendData,
                             args=(clientSocket, sendingQueue
                                   )).start()

    def getActiveClients(self) -> [int]:
        result = []
        for i in range(len(self.__sockets)):
            if self.__sockets[i].active:
                result.append(result)
        return result

    def readData(self, socketID: int) -> bytes:
        return self.__sockets[socketID].receivingQueue.get(block=False)

    def writeData(self, socketID: int, data: bytes) -> NoReturn:
        self.__sockets[socketID].receivingQueue.put(data)

    def __receiveData(
            self,
            clientSocket: socket.socket,
            receivingQueue: Queue):
        while True:
            data = self.__receivePackage(clientSocket)
            receivingQueue.put(data)

    def __sendData(
            self,
            clientSocket: socket.socket,
            sendingQueue: Queue):
        while True:
            data = sendingQueue.get()
            self.__sendPackage(clientSocket, data)

    @staticmethod
    def __receivePackage(clientSocket: socket.socket) -> bytes:
        data = b''
        payloadSize = struct.calcsize(">L")
        while len(data) < payloadSize:
            data += clientSocket.recv(4096)

        packedDataSize = data[:payloadSize]
        data = data[payloadSize:]
        dataSize = struct.unpack(">L", packedDataSize)[0]

        while len(data) < dataSize:
            data += clientSocket.recv(4096)

        data = data[:dataSize]
        return data

    @staticmethod
    def __sendPackage(clientSocket: socket.socket, data: bytes):
        clientSocket.sendall(struct.pack(">L", len(data)) + data)


if __name__ == '__main__':
    dataManager = DataManager(host='0.0.0.0',
                              port=5000,
                              logLevel=logging.DEBUG)
    dataManager.run()
