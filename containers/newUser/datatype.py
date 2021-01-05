import cv2
import threading
import socket
from abc import abstractmethod
from broker import Broker
from typing import Any
from queue import Queue
from collections import defaultdict
from dataManagerClient import DataManagerClient


class NodeSpecs:
    def __init__(self, cores, ram, disk, network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network

    def info(self):
        return "\
                Cores: %d\n\
                ram: %d GB\n\
                disk: %d GB\n\
                network: %d Mbps\n" % (self.cores, self.ram, self.disk, self.cores)


class Master:

    def __init__(self, masterID: int = 0, dataManager: DataManagerClient = None):
        self.masterID: int = masterID
        self.dataManager: DataManagerClient = dataManager


class Client:

    def __init__(self, socketID: int, socket_: socket.socket, sendingQueue: Queue[bytes], receivingQueue: Queue[bytes]):
        self.socketID: int = socketID
        self.socket: socket.socket = socket_
        self.sendingQueue: Queue[bytes] = sendingQueue
        self.receivingQueue: Queue[bytes] = receivingQueue
        self.active = True


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


class User:

    def __init__(self, userID: int, socketID: str):
        self.userID = userID
        self.socketID = socketID


class Task:

    def __init__(self, taskID: int, userID: int, inputData):
        self.taskID = taskID
        self.userID = userID
        self.inputData = inputData
        self.workerID = None
        self.outputData = None
        self.hasDone = False


class ApplicationUserSide:

    def __init__(self, appID: int, broker: Broker, videoPath=None):
        self.appID = appID
        self.appName = None
        self.broker: Broker = broker
        self.capture = cv2.VideoCapture(0) if videoPath is None \
            else cv2.VideoCapture(videoPath)
        self.lockData: threading.Lock = threading.Lock()
        self.dataID = -1
        self.data: dict[int, Any] = {}
        self.result: dict[int, Queue] = defaultdict(Queue)
        self.dataIDSubmittedQueue = Queue()

    def createDataFrame(self, data: Any) -> (int, Any):
        self.lockData.acquire()
        self.dataID += 1
        dataID = self.dataID
        self.lockData.release()
        self.data[dataID] = data
        return dataID

    @abstractmethod
    def run(self):
        pass
