import socket
from queue import Queue
from typing import List
from abc import abstractmethod
from time import time


class IO:
    def __init__(self):
        self.receivedSize: int = 0
        self.sentSize: int = 0


class NodeSpecs:
    def __init__(self, cores, ram, disk, network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network

    def info(self):
        return "Cores: %d\tRam: %d GB\tDisk: %d GB\tNetwork: %d Mbps" % (self.cores, self.ram, self.disk, self.network)


class ApplicationUserSide:

    def __init__(self, appID: int, appName: str = 'UNNAMED'):
        self.appID = appID
        self.appName = appName

    @abstractmethod
    def process(self, inputData):
        pass


class ConnectionIO:

    def __init__(self):
        self.__received: int = 0
        self.__receivedCount: int = 0
        self.__sent: int = 0
        self.__sentCount: int = 0
        self.receivedPerSecond = 0
        self.sentPerSecond = 0
        self.__t = time()
        self.__lastReceived = 0
        self.__lastSent = 0

    def received(self, bytes_: int):
        self.__received += bytes_
        self.__receivedCount += 1
        t = time()
        t_diff = t - self.__t
        if t_diff > 1:
            self.__t = t
            self.receivedPerSecond = (self.__received - self.__lastReceived) / t_diff
            self.__lastReceived = self.__received

    def sent(self, bytes_: int):
        self.__sent += bytes_
        self.__sentCount += 1
        t = time()
        t_diff = t - self.__t
        if t_diff > 1:
            self.__t = t
            self.sentPerSecond = (self.__sent - self.__lastSent) / t_diff
            self.__lastSent = self.__sent

    def averageReceived(self) -> float:
        if self.__receivedCount == 0:
            return 0
        return self.__received / self.__receivedCount

    def averageSent(self) -> float:
        if self.__sentCount == 0:
            return 0
        return self.__sent / self.__sentCount


class Client:

    def __init__(
            self,
            socketID: int,
            socket_: socket.socket,
            sendingQueue: Queue[bytes],
            receivingQueue: Queue[bytes],
            connectionIO: ConnectionIO
    ):
        self.socketID: int = socketID
        self.socket: socket.socket = socket_
        self.sendingQueue: Queue[bytes] = sendingQueue
        self.receivingQueue: Queue[bytes] = receivingQueue
        self.active = True
        self.activeTime = time()
        self.name: str = 'None'
        self.connectionIO: ConnectionIO = connectionIO

    def updateActiveTime(self):
        self.activeTime = time()


class Master:

    def __init__(self, host: str, port: int, masterID: int = 0):
        self.host = host
        self.port = port
        self.masterID = masterID


class Worker(Client):

    def __init__(
            self,
            socketID: int,
            socket_: socket.socket,
            sendingQueue: Queue[bytes],
            receivingQueue: Queue[bytes],
            workerID: int,
            specs: NodeSpecs,
            ownedBy: int,
            connectionIO: ConnectionIO
    ):
        super(Worker, self).__init__(
            socketID=socketID,
            socket_=socket_,
            sendingQueue=sendingQueue,
            receivingQueue=receivingQueue,
            connectionIO=connectionIO
        )

        self.workerID: int = workerID
        self.specs: NodeSpecs = specs
        self.token = None
        self.ip = None
        self.port = None
        self.ownedBy: int = ownedBy


class User(Client):

    def __init__(
            self,
            socketID: int,
            socket_: socket.socket,
            sendingQueue: Queue[bytes],
            receivingQueue: Queue[bytes],
            userID: int,
            appRunMode: str,
            appIDs: List[int],
            connectionIO: ConnectionIO,
            workerByAppID: dict[int, Worker] = None,
    ):
        super(User, self).__init__(
            socketID=socketID,
            socket_=socket_,
            sendingQueue=sendingQueue,
            receivingQueue=receivingQueue,
            connectionIO=connectionIO
        )
        self.userID = userID
        self.appRunMode = appRunMode
        self.appIDs = appIDs
        self.isReady = False
        self.appIDTokenMap = {}
        if workerByAppID is None:
            self.workerByAppID: dict[int, Worker] = {}

    def verifyWorker(self, appID: int, token: str, worker: Worker) -> bool:
        if appID in self.appIDTokenMap \
                and self.appIDTokenMap[appID] == token:
            self.workerByAppID[appID] = worker
            if len(self.appIDTokenMap) == len(self.workerByAppID):
                self.isReady = True
            return True
        return False


class Task:

    def __init__(self, workerID: int, userID: int, taskID: int, appID: int, dataID: int):
        self.workerID = workerID
        self.userID = userID
        self.taskID = taskID
        self.appID = appID
        self.dataID = dataID
        self.resultID = None
        self.hasDone = False
