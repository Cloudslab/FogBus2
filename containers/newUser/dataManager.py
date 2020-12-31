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
        self.receivingQueue: Queue[bytes] = Queue()
        self.sendingQueue: Queue[bytes] = Queue()
        self.clientSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.logger = get_logger('User-DataManager', logLevel)

    def run(self):
        self.clientSocket.connect((self.host, self.port))

        threading.Thread(target=self.__receiver).start()
        threading.Thread(target=self.__sender).start()
        self.logger.info("[*] Connected to %s:%d over tcp.", self.host, self.port)

    def __receiver(self):
        buffer = b''
        payloadSize = struct.calcsize('>L')

        while True:
            while len(buffer) < payloadSize:
                buffer += self.clientSocket.recv(4096)

            packedDataSize = buffer[:payloadSize]
            buffer = buffer[payloadSize:]
            dataSize = struct.unpack('>L', packedDataSize)[0]

            while len(buffer) < dataSize:
                buffer += self.clientSocket.recv(4096)

            data = buffer[:dataSize]
            buffer = buffer[dataSize:]
            self.receivingQueue.put(data)

    def __sender(self):
        while True:
            data = self.sendingQueue.get()
            self.clientSocket.sendall(struct.pack(">L", len(data)) + data)


if __name__ == '__main__':
    dataManager = DataManager(host='0.0.0.0',
                              port=5000,
                              logLevel=logging.DEBUG)
    dataManager.run()
