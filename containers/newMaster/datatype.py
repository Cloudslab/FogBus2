import socket
import threading
from queue import Queue
from typing import List
from abc import abstractmethod
from time import time, sleep


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
        self.__lastReceiveTime = 0
        self.__lastTotalReceived = 0
        self.__lastSendTime = 0
        self.__lastTotalSent = 0
        self.averageReceivedPackageSize = 0
        self.averageSentPackageSize = 0
        self.lowestReceivingSpeed = 0
        self.highestReceivingSpeed = 0
        self.averageReceivingSpeed = 0
        self.lowestSendingSpeed = 0
        self.highestSendingSpeed = 0
        self.averageSendingSpeed = 0

        self.__run()

    def __run(self):
        threads = [
            self.__averageReceivedPackageSize,
            self.__averageSentPackageSize,
            self.__averageReceivingSpeed,
            self.__averageSendingSpeed,
        ]
        for t in threads:
            threading.Thread(
                target=t
            ).start()

    def received(self, bytes_: int):
        self.__received += bytes_
        self.__receivedCount += 1
        if self.__lastReceiveTime == 0:
            self.__lastReceiveTime = time()
            self.__lastTotalReceived = self.__received

    def sent(self, bytes_: int):
        self.__sent += bytes_
        self.__sentCount += 1
        if self.__lastSendTime == 0:
            self.__lastSendTime = time()
            self.__lastTotalSent = self.__sent

    def __averageReceivedPackageSize(self):
        while True:
            sleep(1)
            if self.__receivedCount == 0:
                continue
            self.averageReceivedPackageSize = self.__received / self.__receivedCount

    def __averageSentPackageSize(self):
        while True:
            sleep(1)
            if self.__sentCount == 0:
                continue
            self.averageSentPackageSize = self.__sent / self.__sentCount

    def __averageReceivingSpeed(self):

        while True:
            sleep(1)
            if self.__lastReceiveTime == 0:
                continue
            self.averageReceivingSpeed, \
            self.lowestReceivingSpeed, \
            self.highestReceivingSpeed, \
            self.__lastReceiveTime, \
            self.__lastTotalReceived = self.__speedCalculator(
                self.__lastReceiveTime,
                self.__lastTotalReceived,
                self.__received,
                self.lowestReceivingSpeed,
                self.highestReceivingSpeed
            )

    def __averageSendingSpeed(self):

        while True:
            sleep(1)
            if self.__lastSendTime == 0:
                continue
            self.averageSendingSpeed, \
            self.lowestSendingSpeed, \
            self.highestSendingSpeed, \
            self.__lastSendTime, \
            self.__lastTotalSent = self.__speedCalculator(
                self.__lastSendTime,
                self.__lastTotalSent,
                self.__sent,
                self.lowestSendingSpeed,
                self.highestSendingSpeed
            )

    @staticmethod
    def __speedCalculator(lastTime, lastSize, total, lowest, highest):

        currentTime = time()
        timeDiff = currentTime - lastTime
        receivedDiff = total - lastSize
        average = receivedDiff / timeDiff
        if average > highest:
            highest = average
        if lowest == 0:
            lowest = average
        elif average < lowest:
            lowest = average

        return average, lowest, highest, currentTime, total


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
