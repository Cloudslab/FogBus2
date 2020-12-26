import logging
import threading
import struct
import socket

from logger import get_logger
from queue import Queue
from message import Message


class DataManager:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.dataID = 0
        self.host: str = host
        self.port: int = port
        self.clientSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = get_logger('Master-MainService', logLevel)

    def run(self):
        self.clientSocket.connect((self.host, self.port))
        receivingQueue = Queue()
        sendingQueue = Queue()
        threading.Thread(target=self.receiveData,
                         args=(self.clientSocket, receivingQueue
                               )).start()
        threading.Thread(target=self.sendData,
                         args=(self.clientSocket, sendingQueue
                               )).start()
        self.logger.info("[*] Connected to %s:%d over tcp.", self.host, self.port)

    def receiveData(self, clientSocket: socket.socket, receivingQueue: Queue):
        while True:
            data = self.receivePackage(clientSocket)
            receivingQueue.put(data)

    def sendData(self, clientSocket: socket.socket, sendingQueue: Queue):
        while True:
            data = sendingQueue.get()
            self.sendPackage(clientSocket, data)

    @staticmethod
    def receivePackage(clientSocket: socket.socket) -> bytes:
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
    def sendPackage(clientSocket: socket.socket, data: bytes):
        clientSocket.sendall(struct.pack(">L", len(data)) + data)


if __name__ == '__main__':
    dataManager = DataManager(host='0.0.0.0',
                              port=5000,
                              logLevel=logging.DEBUG)
    dataManager.run()
