import logging
import threading
import struct
import socket
from logger import get_logger
from queue import Queue
from datatype import Worker


class DataManagerServer:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.host: str = host
        self.port: int = port
        self.__currentSocketID = 0
        self.__lockSocketID: threading.Lock = threading.Lock()
        self.unregisteredClients: Queue[Worker] = Queue()
        self.__serverSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = get_logger('Worker-DataManagerServer', logLevel)

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
        self.logger.info('[*] Serves at %s:%d over tcp.', self.host, self.port)
        while True:
            clientSocket, _ = self.__serverSocket.accept()

            socketID = self.__newSocketID()
            worker = Worker(
                socketID=socketID,
                socket_=clientSocket,
                receivingQueue=Queue(),
                sendingQueue=Queue())
            worker.link()
            self.unregisteredClients.put(worker)

    @staticmethod
    def __receiver(worker: Worker):
        buffer = b''
        payloadSize = struct.calcsize('>L')

        while True:
            try:
                while len(buffer) < payloadSize:
                    buffer += worker.socket.recv(4096)

                packedDataSize = buffer[:payloadSize]
                buffer = buffer[payloadSize:]
                dataSize = struct.unpack('>L', packedDataSize)[0]

                while len(buffer) < dataSize:
                    buffer += worker.socket.recv(4096)

                data = buffer[:dataSize]
                buffer = buffer[dataSize:]
                worker.receivingQueue.put(data)
            except OSError:
                worker.active = False
                break

    @staticmethod
    def __sender(worker: Worker):
        while True:

            try:
                data = worker.sendingQueue.get()
                worker.socket.sendall(struct.pack(">L", len(data)) + data)
            except OSError:
                worker.active = False
                break


if __name__ == '__main__':
    dataManager = DataManagerServer(host='0.0.0.0',
                                    port=5000,
                                    logLevel=logging.DEBUG)
    dataManager.run()
