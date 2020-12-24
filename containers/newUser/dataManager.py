import logging
import socket
import threading
import queue
import struct

from logger import get_logger
from typing import Callable
from message import Message


class DataManager:

    def __init__(self, host: str, portReceiving: int, portSending: int, logLevel=logging.DEBUG):

        self.host: str = host
        self.portReceiving: int = portReceiving
        self.portSending: int = portSending

        self.senderSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiverSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = get_logger('DataManager', logLevel)

    def connect(self):
        self.senderSocket.connect((self.host, self.portSending))
        self.logger.debug("Sender connected.")
        self.receiverSocket.connect((self.host, self.portReceiving))
        self.logger.debug("Receiver connected.")

    @staticmethod
    def _client(host: str, port: int, handler: Callable):
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        threading.Thread(target=handler, args=(clientSocket,)).start()

    @staticmethod
    def receiveMessage(clientSocket: socket.socket) -> bytes:
        data = b""
        payloadSize = struct.calcsize(">L")
        while len(data) < payloadSize:
            data += clientSocket.recv(4096)

        packedDataSize = data[:payloadSize]
        data = data[payloadSize:]
        dataSize = struct.unpack(">L", packedDataSize)[0]

        while len(data) < dataSize:
            data += clientSocket.recv(4096)

        data = data[:dataSize]
        return Message.decrypt(data)

    @staticmethod
    def sendMessage(clientSocket, data):
        dataEncrypted = Message.encrypt(data)
        clientSocket.sendall(struct.pack(">L", len(dataEncrypted)) + dataEncrypted)

    def sendData(self, data):
        self.sendMessage(self.senderSocket, data)
        dataID = self.receiveMessage(self.senderSocket)
        self.logger.debug("Sent data, got id: %d", dataID)
        return dataID

    def receiveData(self, dataID):
        self.sendMessage(self.receiverSocket, dataID)
        self.logger.debug("Receiving data: %d", dataID)
        data = self.receiveMessage(self.receiverSocket)
        self.logger.debug("Received data: %d", dataID)
        return data


if __name__ == '__main__':
    dataManager = DataManager(host='0.0.0.0',
                              portSending=5001,
                              portReceiving=5002,
                              logLevel=logging.DEBUG)
    dataManager.connect()

    dataID = dataManager.sendData(999)
    data = dataManager.receiveData(dataID)
    print(data)