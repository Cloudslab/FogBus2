import socket
from queue import Queue
from typing import List
from abc import abstractmethod


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
            userByAppID: dict[int, Client] = None):
        super(Worker, self).__init__(
            socketID=socketID,
            socket_=socket_,
            sendingQueue=sendingQueue,
            receivingQueue=receivingQueue)

        self.workerID: int = workerID
        self.specs: NodeSpecs = specs
        if userByAppID is None:
            self.userByAppID: dict[int, User] = {}


class User(Client):

    def __init__(
            self,
            socketID: int,
            socket_: socket.socket,
            sendingQueue: Queue[bytes],
            receivingQueue: Queue[bytes],
            userID: int,
            workerByAppID: dict[int, Worker] = None):
        super(User, self).__init__(
            socketID=socketID,
            socket_=socket_,
            sendingQueue=sendingQueue,
            receivingQueue=receivingQueue)
        self.userID = userID
        if workerByAppID is None:
            self.workerByAppID: dict[int, Worker] = {}


class Task:

    def __init__(self, workerID: int, userID: int, taskID: int, appID: int, dataID: int):
        self.workerID = workerID
        self.userID = userID
        self.taskID = taskID
        self.appID = appID
        self.dataID = dataID
        self.resultID = None
        self.hasDone = False
