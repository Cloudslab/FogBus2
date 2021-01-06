import logging
import threading
import struct
import socket
import os

from queue import Empty
from time import sleep
from logger import get_logger
from message import Message
from typing import NoReturn, Any, List
from collections import defaultdict
from time import time
from secrets import token_urlsafe
from queue import Queue
from abc import abstractmethod


class NodeSpecs:
    def __init__(self, cores, ram, disk, network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network

    def info(self):
        return "Cores: %d\tRam: %d GB\tDisk: %d GB\tNetwork: %d Mbps" % (self.cores, self.ram, self.disk, self.network)


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
        self.host: str = host
        self.port: int = port
        self.activeTime = time()

        if receivingQueue is None:
            self.receivingQueue: Queue[bytes] = Queue()
        else:
            self.receivingQueue: Queue[bytes] = receivingQueue

        if sendingQueue is None:
            self.sendingQueue: Queue[bytes] = Queue()
        else:
            self.sendingQueue: Queue[bytes] = sendingQueue

        self.socket = socket_
        self.logger = get_logger('Worker-%s-DataManager' % self.name, logLevel)

    def link(self):
        if self.socket is None \
                and self.host is not None \
                and self.port is not None:
            self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            threading.Thread(target=self.__receiver).start()
            threading.Thread(target=self.__sender).start()
            threading.Thread(target=self.__keepAlive).start()

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

    def updateActiveTime(self):
        self.activeTime = time()

    def __keepAlive(self):
        while True:
            self.sendingQueue.put(b'alive')
            if time() - self.activeTime > 2:
                self.socket.close()
                self.isConnected = False
                break
            sleep(1)
        self.logger.warning("Master disconnected")
        os._exit(0)

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


class Worker(DataManagerClient):
    def __init__(
            self,
            name: str = None,
            host: str = None,
            port: int = None,
            socket_: socket.socket = None,
            receivingQueue: Queue = None,
            sendingQueue: Queue = None,
            workerID: int = None,
            socketID: int = None,
            logLevel=logging.DEBUG):
        DataManagerClient.__init__(
            self,
            name=name,
            host=host,
            port=port,
            socket_=socket_,
            receivingQueue=receivingQueue,
            sendingQueue=sendingQueue,
            logLevel=logLevel
        )
        self.workerID = workerID
        self.socketID = socketID


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

    def __keepAlive(self, worker: Worker):
        while True:
            worker.sendingQueue.put(b'alive')
            if time() - worker.activeTime > 2:
                worker.socket.close()
                break
            sleep(1)
        self.logger.debug("Discard worker")

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
                worker.updateActiveTime()
                if not data == b'alive':
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


class Node:

    def __init__(self, dataManager: DataManagerClient = None):
        self.dataManager = dataManager


class Master(DataManagerClient):
    def __init__(
            self,
            name: str = None,
            host: str = None,
            port: int = None,
            socket_: socket.socket = None,
            receivingQueue: Queue = None,
            sendingQueue: Queue = None,
            masterID: int = None,
            logLevel=logging.DEBUG):
        DataManagerClient.__init__(
            self,
            name=name,
            host=host,
            port=port,
            socket_=socket_,
            receivingQueue=receivingQueue,
            sendingQueue=sendingQueue,
            logLevel=logLevel
        )
        self.masterID = masterID


class ApplicationUserSide:

    def __init__(self, appID: int, appName: str = 'UNNAMED'):
        self.appID = appID
        self.appName = appName

    @abstractmethod
    def process(self, inputData):
        pass


class Broker:

    def __init__(
            self,
            masterIP: str,
            masterPort: int,
            thisIP: str,
            thisPort: int,
            app: ApplicationUserSide = None,
            userID: int = None,
            appID: int = None,
            token: str = None,
            logLevel=logging.DEBUG):
        self.logger = get_logger('Worker-Broker', logLevel)
        self.masterIP = masterIP
        self.masterPort = masterPort
        self.thisIP = thisIP
        self.thisPort = thisPort
        self.app: ApplicationUserSide = app
        self.token: str = token
        self.userID: int = userID
        self.appID: int = appID
        self.workerID = None
        self.messageByAppID: dict[int, Queue] = defaultdict(Queue)
        self.master: Master = Master(
            name='Master',
            host=self.masterIP,
            port=self.masterPort,
            logLevel=self.logger.level
        )

        self.workers: List[Worker] = []
        self.service: DataManagerServer = DataManagerServer(
            host=self.thisIP,
            port=thisPort)

    def run(self):
        if self.app is not None:
            self.service.run()

        self.master.link()
        threading.Thread(target=self.__receivedMessageHandler).start()
        self.__register()

    def __handleClients(self):

        while True:
            worker = self.service.unregisteredClients.get()
            registrationInfo = worker.receivingQueue.get()
            registrationInfo = Message.decrypt(registrationInfo)
            workerID = registrationInfo['workerID']
            worker.workerID = workerID
            self.workers[workerID] = worker

    def __register(self) -> NoReturn:
        message = {'type': 'register',
                   'role': 'worker',
                   'ip': self.thisIP,
                   'port': self.thisPort,
                   'userID': self.userID,
                   'appID': self.appID,
                   'token': self.token,
                   'nodeSpecs': NodeSpecs(1, 2, 3, 4)}
        self.__sendTo(self.master, message)
        self.logger.info("[*] Registering ...")
        while self.workerID is None:
            pass
        self.logger.info("[*] Registered with workerID-%d", self.workerID)

    @staticmethod
    def __sendTo(target: DataManagerClient, message: Any) -> NoReturn:
        target.sendingQueue.put(Message.encrypt(message))

    def __receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.master.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'workerID':
                self.workerID = message['workerID']
            elif message['type'] == 'runWorker':
                userID = message['userID']
                appID = message['appID']
                token = message['token']
                self.__runWorker(
                    userID=userID,
                    appID=appID,
                    token=token)
            elif message['type'] == 'data':
                appID = message['appIDs'][0]
                self.messageByAppID[appID].put(message)

    @staticmethod
    def __runWorker(userID: int, appID: int, token: str):
        os.system("python worker.py %d %d %s > /dev/null 2>&1 &" % (userID, appID, token))

    def __runApp(self, app: ApplicationUserSide):
        self.logger.info('[*] AppID-%d-{%s} is serving ...', app.appID, app.appName)
        while True:
            message = self.messageByAppID[app.appID].get()
            self.__executeApp(app, message)

    def __executeApp(self, app: ApplicationUserSide, message) -> NoReturn:
        self.logger.debug('Executing appID-%d ...', app.appID)
        data = message['data']
        result = app.process(data)
        message['type'] = 'submitResult'
        message['workerID'] = self.workerID
        message['appID'] = app.appID
        message['appIDs'] = message['appIDs'][1:]

        t = time() - message['time'][0]
        message['time'].append(t)

        if len(message['appIDs']):
            message['data'] = result
        else:
            del message['data']
            message['result'] = result
        self.__sendTo(self.master, message)
        self.logger.debug('Executed appID-%d and returned the result', app.appID)


if __name__ == '__main__':
    from apps import TestApp

    apps = [TestApp(appID=42)]
    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        thisIP='127.0.0.1',
        thisPort=6000,
        appIDs=apps,
        logLevel=logging.DEBUG)
    broker.run()
