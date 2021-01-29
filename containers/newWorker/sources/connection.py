import socket
import struct
import threading
import traceback
import pickle
from time import sleep, time
from queue import Queue, PriorityQueue
from typing import Dict, Tuple, List
from exceptions import *

Address = Tuple[str, int]


def encrypt(obj) -> bytes:
    data = pickle.dumps(obj, 0)
    return data


def decrypt(msg: bytes) -> Dict:
    try:
        obj = pickle.loads(msg, fix_imports=True, encoding="bytes")
        return obj
    except Exception:
        traceback.print_exc()


class Identity:
    def __init__(
            self,
            role: str = None,
            id_: int = None,
            addr: Address = None,
            name: str = None,
            nameLogPrinting: str = None,
            nameConsistent: str = None,
            machineID: str = None):
        self.role: str = role
        self.id: int = id_
        self.addr: Address = addr
        self.name: str = name
        self.nameLogPrinting: str = nameLogPrinting
        self.nameConsistent: str = nameConsistent
        self.machineID: str = machineID


class Source(Identity):

    def __init__(
            self,
            role: str,
            id_: int,
            name: str,
            nameLogPrinting: str,
            nameConsistent: str,
            machineID: str,
            addr: Address):
        super().__init__(
            role=role,
            id_=id_,
            name=name,
            addr=addr,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            machineID=machineID
        )


class Average(Identity):

    def __init__(
            self,
            role: str = None,
            id_: int = None,
            addr: Address = None,
            name: str = None,
            nameLogPrinting: str = None,
            nameConsistent: str = None,
            machineID: str = None):
        super().__init__(
            role=role,
            id_=id_,
            addr=addr,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            machineID=machineID
        )
        self.__maxRecordNumber = 100
        self.__index = 0
        self.__table: List[int] = [0 for _ in range(self.__maxRecordNumber)]

    def update(self, bytes_):
        self.__table[self.__index] = bytes_
        self.__index = (self.__index + 1) % self.__maxRecordNumber

    def average(self):
        total = 0
        count = 0
        for record in self.__table:
            if record == 0:
                break
            total += record
            count += 1

        if count == 0:
            return None
        return total / count

    def __str__(self):
        return str(self.average())


class Connection:
    def __init__(self, addr):
        self.addr = addr

    def __send(self, message: bytes, retries: int = 3):
        clientSocket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM)
        try:
            clientSocket.settimeout(3)
            clientSocket.connect(self.addr)
            package = struct.pack(">L", len(message)) + message
            clientSocket.sendall(package)
            clientSocket.settimeout(None)
            clientSocket.close()
        except OSError:
            clientSocket.close()
            if retries:
                self.__send(message=message, retries=retries - 1)
                return
            raise OSError
        except ConnectionRefusedError:
            clientSocket.close()
            if retries:
                sleep(0.5)
                self.__send(message=message, retries=retries - 1)
                return
            raise ConnectionRefusedError

    def send(self, message: Dict, retries: int = 10):
        message['_sentAt'] = time() * 1000
        self.__send(encrypt(message), retries=retries)


class Request:

    def __init__(self, clientSocket: socket.socket, clientAddr):
        self.clientSocket: clientSocket = clientSocket
        self.clientAddr = clientAddr


class Message:
    def __init__(self, content: Dict):
        self.content: Dict = content

        if 'source' not in self.content:
            raise MessageDoesNotContainSourceInfo

        if 'type' not in self.content:
            raise MessageDoesNotContainType

        self.type = self.content['type']
        self.source: Source = self.content['source']

    def __lt__(self, other):
        if self.type == other.type:
            return False
        if self.type in {'ping', 'pong'}:
            return False
        return True


class Server:

    def __init__(
            self,
            addr,
            messagesQueue: PriorityQueue[Tuple[Message, int]],
            threadNumber: int = 256):
        self.addr = addr
        self.serverSocket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM)
        self.messageQueue: PriorityQueue[Tuple[Message, int]] = messagesQueue

        self.threadNumber: int = threadNumber
        self.requests: Queue[Request] = Queue()
        self.run()

    def run(self):
        for i in range(self.threadNumber):
            t = threading.Thread(
                target=self.__handleThread,
                name="HandlingThread-%d" % i
            )
            t.start()
        server = threading.Thread(
            target=self.__serve,
            name="Server"
        )
        server.start()

    def __serve(self):
        try:
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.serverSocket.bind(self.addr)
            self.serverSocket.listen()
            while True:
                clientSocket, clientAddress = self.serverSocket.accept()
                request = Request(clientSocket, clientAddress)
                self.requests.put(request)
        except socket.error:
            self.serverSocket.close()
            raise CannotBindAddr

    def __handleThread(self):
        while True:
            request = self.requests.get()
            content, messageSize = self.__receiveMessage(request.clientSocket)
            if messageSize == 0:
                continue
            message = Message(content=content)
            self.messageQueue.put((message, messageSize))

    @staticmethod
    def __receiveMessage(clientSocket: socket.socket) -> Tuple[Dict, int]:
        result = None
        buffer = b''
        payloadSize = struct.calcsize('>L')

        try:
            clientSocket.settimeout(3)
            while len(buffer) < payloadSize:
                buffer += clientSocket.recv(4096)

            packedDataSize = buffer[:payloadSize]
            buffer = buffer[payloadSize:]
            dataSize = struct.unpack('>L', packedDataSize)[0]

            while len(buffer) < dataSize:
                buffer += clientSocket.recv(4096)

            data = buffer[:dataSize]
            result = data

        except (OSError, socket.error):
            pass

        clientSocket.close()
        if result is None:
            return {}, 0
        # may broken why?
        try:
            res = decrypt(result)
            _receivedAt = time() * 1000
            res['delay'] = _receivedAt - res['_sentAt']
            res['_receivedAt'] = _receivedAt
        except KeyError:
            print(res)
            import traceback
            traceback.print_exc()
        return res, len(result)


if __name__ == '__main__':
    pass
