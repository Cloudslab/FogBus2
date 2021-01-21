import socket
import threading
from queue import Queue
from typing import List, Dict
from abc import abstractmethod
from time import time, sleep
from secrets import token_urlsafe
from connection import Connection


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
            name: str,
            addr,
            connectionIO: ConnectionIO
    ):
        self.name: str = name
        self.addr = addr
        self.connectionIO: ConnectionIO = connectionIO


class Master:

    def __init__(self, host: str, port: int, masterID: int = 0):
        self.host = host
        self.port = port
        self.masterID = masterID


class Worker(Client):

    def __init__(
            self,
            addr,
            name: str,
            workerID: int,
            connectionIO: ConnectionIO,
    ):
        # TODO Containers info
        if name is None:
            name = "Worker-%d" % workerID
        super(Worker, self).__init__(
            name=name,
            addr=addr,
            connectionIO=connectionIO
        )

        self.id: int = workerID


class TaskHandler(Client):

    def __init__(
            self,
            addr,
            taskHandlerID: int,
            taskName: str,
            token: str,
            runningOnWorker: int,
            connectionIO: ConnectionIO,
            user,
            name: str = None,
    ):
        if name is None:
            name = 'TaskHandler-%d' % taskHandlerID
        super(TaskHandler, self).__init__(
            name=name,
            addr=addr,
            connectionIO=connectionIO
        )

        self.id: int = taskHandlerID
        self.taskName = taskName
        self.token = token
        self.runningOnWorker: int = runningOnWorker
        self.user: User = user


class UserTask:
    def __init__(self, token: str, childTaskTokens=None):
        if childTaskTokens is None:
            childTaskTokens = []
        self.token: str = token
        self.childTaskTokens: List[str] = childTaskTokens


class User(Client):

    def __init__(
            self,
            addr,
            userID: int,
            appName: int,
            connectionIO: ConnectionIO,
            name: str,
            taskHandlerByTaskName: dict[int, Worker] = None,
    ):
        if name is None:
            name = 'User-%d' % userID
        super(User, self).__init__(
            name=name,
            addr=addr,
            connectionIO=connectionIO
        )
        self.id = userID
        self.appName = appName
        self.taskNameTokenMap: Dict[str, UserTask] = {}
        if taskHandlerByTaskName is None:
            self.taskHandlerByTaskName: dict[str, TaskHandler] = {}
        self.entranceTasksByName: List[str] = []
        self.respondMessageQueue: Queue = Queue()

    def generateToken(self, taskName: str):
        token = token_urlsafe(16)
        self.taskNameTokenMap[taskName] = UserTask(
            token=token)
        return token

    def verifyTaskHandler(
            self, taskName: str,
            taskHandler: TaskHandler) -> bool:
        if taskName in self.taskNameTokenMap \
                and self.taskNameTokenMap[taskName].token == taskHandler.token:
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
