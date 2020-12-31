import logging
import threading
import struct
import socket
from logger import get_logger
from queue import Queue
from typing import NoReturn
from datatype import Client


class DataManager:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.host: str = host
        self.port: int = port
        self.__currentSocketID = 0
        self.__lockSocketID: threading.Lock = threading.Lock()
        self.__sockets: dict[int, Client] = {}
        self.unregisteredClients: Queue[Client] = Queue()
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

            socketID = self.__newSocketID()
            client = Client(
                socketID=socketID,
                socket_=clientSocket,
                receivingQueue=Queue(),
                sendingQueue=Queue())
            self.__sockets[socketID] = client
            self.unregisteredClients.put(client)
            threading.Thread(target=self.__receiver,
                             args=(client,)).start()
            threading.Thread(target=self.__sender,
                             args=(client,)).start()

    def readData(self, client: Client) -> bytes:
        return self.__sockets[client.socketID].receivingQueue.get(timeout=1)

    def writeData(self, client: Client, data: bytes) -> NoReturn:
        self.__sockets[client.socketID].sendingQueue.put(data)

    def discard(self, client: Client):
        client.active = False
        client.socket.shutdown(socket.SHUT_RDWR)
        del self.__sockets[client.socketID]

    @staticmethod
    def __receiver(client: Client):
        buffer = b''
        payloadSize = struct.calcsize('>L')

        while True:
            try:
                while len(buffer) < payloadSize:
                    buffer += client.socket.recv(4096)

                packedDataSize = buffer[:payloadSize]
                buffer = buffer[payloadSize:]
                dataSize = struct.unpack('>L', packedDataSize)[0]

                while len(buffer) < dataSize:
                    buffer += client.socket.recv(4096)

                data = buffer[:dataSize]
                buffer = buffer[dataSize:]
                client.receivingQueue.put(data)
            except OSError:
                client.active = False
                break

    @staticmethod
    def __sender(client: Client):
        while True:

            try:
                data = client.sendingQueue.get()
                client.socket.sendall(struct.pack(">L", len(data)) + data)
            except OSError:
                client.active = False
                break


if __name__ == '__main__':
    dataManager = DataManager(host='0.0.0.0',
                              port=5000,
                              logLevel=logging.DEBUG)
    dataManager.run()
