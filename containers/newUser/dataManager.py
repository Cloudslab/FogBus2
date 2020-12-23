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
        self.dataToSend = queue.Queue()
        self.dataToReceive = queue.Queue()
        self.dataReceived = {}
        self.host: str = host
        self.portReceiving: int = portReceiving
        self.portSending: int = portSending
        self.logger = get_logger('DataManager', logLevel)

    def run(self):
        threading.Thread(target=self._client,
                         args=(self.host,
                               self.portSending,
                               self.sendData
                               )).start()

        threading.Thread(target=self._client,
                         args=(self.host,
                               self.portReceiving,
                               self.receiveData
                               )).start()

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
        return data

    @staticmethod
    def sendMessage(clientSocket, data):
        dataEncrypted = Message.encrypt(data)
        clientSocket.sendall(struct.pack(">L", len(dataEncrypted)) + dataEncrypted)

    def sendData(self, clientSocket: socket.socket):
        while True:
            data = self.dataToSend.get()
            self.sendMessage(clientSocket, data)
            self.logger.debug("Sent data")

    def receiveData(self, clientSocket: socket.socket):
        while True:
            request = self.dataToReceive.get()
            dataID = request['dataID']
            self.sendMessage(clientSocket, request)
            self.logger.debug("Receiving data: %d", dataID)
            data = self.receiveMessage(clientSocket)
            self.dataReceived[dataID] = Message.decrypt(data)
            self.logger.debug("Received data: %d", dataID)


if __name__ == '__main__':
    dataManager = DataManager(host='0.0.0.0',
                              portSending=5001,
                              portReceiving=5002,
                              logLevel=logging.DEBUG)
    dataManager.run()

    dataManager.dataToSend.put(999)
    dataManager.dataToReceive.put({"dataID": 1})
