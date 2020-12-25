import logging
import threading
import struct
import socket
from logger import get_logger
from typing import Callable
from message import Message


class DataManager:

    def __init__(self, host: str, portReceiving: int, portSending: int, logLevel=logging.DEBUG):
        self.dataID = 0
        self.host: str = host
        self.portReceiving: int = portReceiving
        self.portSending: int = portSending
        self.data: {bytes} = {}
        self.logger = get_logger('Master-DataManager', logLevel)

    def serve(self):
        threading.Thread(target=self._server,
                         args=(self.host,
                               self.portReceiving,
                               self.receiveData
                               )).start()

        threading.Thread(target=self._server,
                         args=(self.host,
                               self.portSending,
                               self.sendData
                               )).start()

    def _server(self, host: str, port: int, handler: Callable):
        serverSocket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((host, port))
        serverSocket.listen(5)
        self.logger.info("[*] Server starts at %s:%d", host, port)
        while True:
            clientSocket, _ = serverSocket.accept()
            threading.Thread(target=handler, args=(clientSocket,)).start()

    @staticmethod
    def receivePackage(clientSocket: socket.socket) -> bytes:
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
    def sendPackage(clientSocket, data):
        dataEncrypted = Message.encrypt(data)
        clientSocket.sendall(struct.pack(">L", len(dataEncrypted)) + dataEncrypted)

    def receiveData(self, clientSocket: socket.socket):
        # TODO: racing
        self.dataID += 1
        dataID = self.dataID
        self.logger.debug("Receiving dataID-%d", dataID)

        data = self.receivePackage(clientSocket)
        self.sendPackage(clientSocket, dataID)

        self.data[dataID] = data
        self.logger.debug("Received dataID-%d", dataID)

    def sendData(self, clientSocket: socket.socket):
        dataID = self.receivePackage(clientSocket)
        if dataID in self.data:
            self.logger.debug("Sending dataID-%d", dataID)
            data = self.data[dataID]
            self.sendPackage(clientSocket, data)
            self.logger.debug("Sent dataID-%d", dataID)
        else:
            self.logger.debug("Does not have dataID-%d", dataID)


if __name__ == '__main__':
    dataManager = DataManager(host='0.0.0.0',
                              portReceiving=5001,
                              portSending=5002,
                              logLevel=logging.DEBUG)
    dataManager.serve()
