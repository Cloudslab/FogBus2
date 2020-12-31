import cv2
import threading
from abc import abstractmethod
from broker import Broker
from typing import Any
from queue import Queue
from collections import defaultdict


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

    def __init__(self, host: str, port: int, masterID: int = 0):
        self.host = host
        self.port = port
        self.masterID = masterID


class Worker:

    def __init__(self, workerID: int, socketID: str, specs: NodeSpecs):
        self.workerID = workerID
        self.socketID = socketID
        self.specs = specs


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
