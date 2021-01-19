import logging
import threading
import struct
import socket
import sys
from logger import get_logger
from queue import Queue
from typing import NoReturn
from datatype import Client, User, Worker, IO, ConnectionIO
from message import Message
from time import time, sleep


class DataManagerServer:

    def __init__(
            self,
            host: str,
            port: int,
            io: IO = IO(),
            logLevel=logging.DEBUG):
        self.__io = io
        self.host: str = host
        self.port: int = port
        self.__currentSocketID = 0
        self.__lockSocketID: threading.Lock = threading.Lock()
        self.__sockets: dict[int, Client] = {}
        self.unregisteredClients: Queue[Client] = Queue()
        self.__serverSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = get_logger('Master-DataManagerServer', logLevel)

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
                sendingQueue=Queue(),
                connectionIO=ConnectionIO()
            )
            self.__sockets[socketID] = client
            self.unregisteredClients.put(client)
            receiverEvent = threading.Event()
            threading.Thread(target=self.__receiver,
                             args=(client, self.__io, receiverEvent)).start()
            receiverEvent.wait()

            senderEvent = threading.Event()
            threading.Thread(target=self.__sender,
                             args=(client, self.__io, senderEvent)).start()
            senderEvent.wait()

            keepAliveEvent = threading.Event()
            threading.Thread(target=self.__keepAlive,
                             args=(client, keepAliveEvent)).start()
            keepAliveEvent.wait()

    def hasClient(self, client: Client):
        return client.socketID in self.__sockets

    def readData(self, client: Client) -> bytes:
        return self.__sockets[client.socketID].receivingQueue.get(timeout=1)

    def writeData(self, client: Client, data: bytes) -> NoReturn:
        self.__sockets[client.socketID].sendingQueue.put(data)

    def discard(self, client: Client):
        if self.hasClient(client):
            message = {
                'type': 'close',
                'reason': 'disconnect'
            }
            client.sendingQueue.put(Message.encrypt(message))
            if isinstance(client, User):
                for appID, worker in client.taskByName.items():
                    self.discard(worker)
            client.active = False
            client.socket.close()
            del self.__sockets[client.socketID]
            del client

    def __keepAlive(self, client: Client, event: threading.Event):
        event.set()
        while True:

            if not client.sendingQueue.qsize():
                client.sendingQueue.put(b'alive')
            if time() - client.activeTime > 5:
                self.discard(client)
                break
            sleep(1)

    @staticmethod
    def __receiver(client: Client, io: IO, event: threading.Event):
        buffer = b''
        payloadSize = struct.calcsize('>L')
        event.set()
        try:
            while True:

                while len(buffer) < payloadSize:
                    chunk = client.socket.recv(4096)
                    if not chunk:
                        raise OSError
                    buffer += chunk

                packedDataSize = buffer[:payloadSize]
                buffer = buffer[payloadSize:]
                dataSize = struct.unpack('>L', packedDataSize)[0]

                while len(buffer) < dataSize:
                    if dataSize > 5:
                        print('!!!!!!!!!!!!!!!dataSize', dataSize, len(buffer))
                    chunk = client.socket.recv(4096)
                    if not chunk:
                        raise OSError
                    buffer += chunk

                data = buffer[:dataSize]
                buffer = buffer[dataSize:]
                client.updateActiveTime()
                if not data == b'alive':
                    client.connectionIO.received(payloadSize + dataSize)
                    client.receivingQueue.put(data)
                io.receivedSize += sys.getsizeof(data)
        except OSError:
            client.active = False

    @staticmethod
    def __sender(client: Client, nodeIO: IO, event: threading.Event):
        event.set()
        try:
            while True:
                data_ = client.sendingQueue.get()
                data = struct.pack(">L", len(data_)) + data_
                client.socket.sendall(data)
                dataSize = sys.getsizeof(data)
                nodeIO.sentSize += dataSize
                if not data_ == b'alive':
                    client.connectionIO.sent(dataSize)

        except OSError:
            client.active = False


if __name__ == '__main__':
    dataManager = DataManagerServer(host='0.0.0.0',
                                    port=5000,
                                    logLevel=logging.DEBUG)
    dataManager.run()
