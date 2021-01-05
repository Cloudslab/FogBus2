import logging
import threading
import struct
import socket

from logger import get_logger
from queue import Queue, Empty
from typing import NoReturn, Any
from time import time


class DataManagerClient:

    def __init__(
            self,
            name: str = None,
            host: str = None,
            port: int = None,
            socket_: socket.socket = None,
            receivingQueue: Queue = None,
            sendingQueue: Queue = None,
            logLevel=logging.DEBUG):
        self.name = name
        self.dataID = 0
        self.host: str = host
        self.port: int = port

        if receivingQueue is None:
            self.receivingQueue: Queue[bytes] = Queue()
        else:
            self.receivingQueue: Queue[bytes] = receivingQueue

        if sendingQueue is None:
            self.sendingQueue: Queue[bytes] = Queue()
        else:
            self.sendingQueue: Queue[bytes] = sendingQueue

        self.socket = socket_
        self.logger = get_logger('User-%s-DataManager' % self.name, logLevel)
        self.activeTime = time()

    def link(self):
        if self.socket is None \
                and self.host is not None \
                and self.port is not None:
            self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            threading.Thread(target=self.__receiver).start()
            threading.Thread(target=self.__sender).start()

            self.logger.info("[*] %s linked to %s:%d over tcp.", self.name, self.host, self.port)
        else:
            self.logger.info("[*] %s linked.", self.name)

    def read(self) -> Any:
        data = None
        try:
            data = self.receivingQueue.get(block=False)
        except Empty:
            pass
        return data

    def write(self, data) -> NoReturn:
        self.sendingQueue.put(data)

    def __keepAlive(self, ):
        while True:
            self.sendingQueue.put(b'alive')
            if time() - self.activeTime > 1:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.logger.warning("Shutdown socket")

    def __receiver(self):
        buffer = b''
        payloadSize = struct.calcsize('>L')

        try:
            while True:
                while len(buffer) < payloadSize:
                    buffer += self.socket.recv(4096)

                packedDataSize = buffer[:payloadSize]
                buffer = buffer[payloadSize:]
                dataSize = struct.unpack('>L', packedDataSize)[0]

                while len(buffer) < dataSize:
                    buffer += self.socket.recv(4096)

                data = buffer[:dataSize]
                buffer = buffer[dataSize:]
                self.activeTime = time()

                if not data == b'alive':
                    self.receivingQueue.put(data)
        except OSError:
            self.logger.warning("Receiver disconnected.")

    def __sender(self):

        try:
            while True:
                data = self.sendingQueue.get()
                self.socket.sendall(struct.pack(">L", len(data)) + data)
        except OSError:
            self.logger.warning("Sender disconnected.")


if __name__ == '__main__':
    dataManager = DataManagerClient(host='0.0.0.0',
                                    port=5000,
                                    logLevel=logging.DEBUG)
    dataManager.link()
