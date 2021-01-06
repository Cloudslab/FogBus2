import socket
from queue import Queue
from typing import List
from abc import abstractmethod
from time import time


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


class Client:

    def __init__(self, socketID: int, socket_: socket.socket, sendingQueue: Queue[bytes], receivingQueue: Queue[bytes]):
        self.socketID: int = socketID
        self.socket: socket.socket = socket_
        self.sendingQueue: Queue[bytes] = sendingQueue
        self.receivingQueue: Queue[bytes] = receivingQueue
        self.active = True
        self.activeTime = time()

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
            specs: NodeSpecs):
        super(Worker, self).__init__(
            socketID=socketID,
            socket_=socket_,
            sendingQueue=sendingQueue,
            receivingQueue=receivingQueue)

        self.workerID: int = workerID
        self.specs: NodeSpecs = specs
        self.token = None
        self.ip = None
        self.port = None


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
            workerByAppID: dict[int, Worker] = None):
        super(User, self).__init__(
            socketID=socketID,
            socket_=socket_,
            sendingQueue=sendingQueue,
            receivingQueue=receivingQueue)
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
