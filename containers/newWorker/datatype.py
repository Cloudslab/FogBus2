import logging
import threading
import struct
import socket
import os
import sys
import cProfile
import pstats

from queue import Empty
from time import sleep
from logger import get_logger
from message import Message
from typing import NoReturn, Any, List
from collections import defaultdict
from time import time
from queue import Queue
from abc import abstractmethod
from systemInfo import SystemInfo


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


class NodeSpecs:
    def __init__(self, cores, ram, disk, network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network

    def info(self):
        return "Cores: %d\tRam: %d GB\tDisk: %d GB\tNetwork: %d Mbps" % (self.cores, self.ram, self.disk, self.network)


class IO:
    def __init__(self):
        self.receivedSize: int = 0
        self.sentSize: int = 0


class DataManagerClient:

    def __init__(
            self,
            name: str = None,
            host: str = None,
            port: int = None,
            socket_: socket.socket = None,
            receivingQueue: Queue = None,
            sendingQueue: Queue = None,
            io: IO = IO(),
            logLevel=logging.DEBUG):
        self.name = name
        self.host: str = host
        self.port: int = port
        self.activeTime = time()
        self.__io = io
        self.connectionIO = ConnectionIO()

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

            self.logger.info("[*] Linked to %s at %s:%d over tcp.", self.name, self.host, self.port)
        else:
            self.logger.info("[*] Linked to %s.", self.name)

        sender = threading.Event()
        receiver = threading.Event()
        keepAlive = threading.Event()
        threading.Thread(target=self.__receiver, args=(sender,)).start()
        sender.wait()
        threading.Thread(target=self.__sender, args=(receiver,)).start()
        receiver.wait()
        threading.Thread(target=self.__keepAlive, args=(keepAlive,)).start()
        keepAlive.wait()

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

    def __keepAlive(self, event: threading.Event):
        event.set()
        while True:
            if not self.sendingQueue.qsize():
                self.sendingQueue.put(b'alive')
            if time() - self.activeTime > 5:
                if isinstance(self.socket, socket.socket):
                    self.socket.close()
                self.isConnected = False
                break
            sleep(1)
        self.logger.warning("Master disconnected")
        os._exit(0)

    def __receiver(self, event: threading.Event):
        event.set()
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
                    self.connectionIO.received(payloadSize + dataSize)
                    self.receivingQueue.put(data)
                    self.recordDataTransferring()

                self.__io.receivedSize += sys.getsizeof(data)

        except OSError:
            self.logger.warning("Receiver disconnected.")

    def __sender(self, event: threading.Event):
        event.set()
        try:
            while True:
                data_ = self.sendingQueue.get()
                data = struct.pack(">L", len(data_)) + data_
                self.socket.sendall(data)
                dataSize = sys.getsizeof(data)
                self.__io.sentSize += dataSize
                if not data_ == b'alive':
                    self.connectionIO.sent(dataSize)
                    self.recordDataTransferring()
        except OSError:
            self.logger.warning("Sender disconnected.")

    def recordDataTransferring(self):
        if self.name is None:
            return
        filename = 'AverageIO@%s.csv ' % self.name
        fileContent = 'averageReceivedPackageSize, ' \
                      'averageSentPackageSize, ' \
                      'lowestReceivingSpeed, ' \
                      'highestReceivingSpeed, ' \
                      'lowestSendingSpeed, ' \
                      'highestSendingSpeed\r\n' \
                      '%f, %f, %f, %f, %f, %f\r\n' % (
                          self.connectionIO.averageReceivedPackageSize,
                          self.connectionIO.averageSentPackageSize,
                          self.connectionIO.lowestReceivingSpeed,
                          self.connectionIO.highestReceivingSpeed,
                          self.connectionIO.lowestSendingSpeed,
                          self.connectionIO.highestSendingSpeed,
                      )

        self.writeFile(filename, fileContent)

    @staticmethod
    def writeFile(name, content):
        logPath = './log'
        if not os.path.exists(logPath):
            os.mkdir(logPath)
        f = open('%s/%s' % (logPath, name), 'w')
        f.write(content)
        f.close()


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
            io: IO = IO(),
            logLevel=logging.DEBUG):
        DataManagerClient.__init__(
            self,
            name=name,
            host=host,
            port=port,
            socket_=socket_,
            receivingQueue=receivingQueue,
            sendingQueue=sendingQueue,
            io=io,
            logLevel=logLevel
        )
        self.workerID = workerID
        self.socketID = socketID


class DataManagerServer:

    def __init__(
            self,
            host: str,
            port: int = None,
            receivingQueue: Queue = Queue(),
            io: IO = IO(),
            logLevel=logging.DEBUG):
        self.host: str = host
        self.port: int = port
        self.receivingQueue: Queue = receivingQueue
        self.__currentSocketID = 0
        self.__lockSocketID: threading.Lock = threading.Lock()
        self.__serverSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = get_logger('Worker-DataManagerServer', logLevel)
        self.__io = io

    def run(self):
        threading.Thread(target=self.__serve).start()
        while self.port is None:
            pass

    def __newSocketID(self) -> int:
        self.__lockSocketID.acquire()
        self.__currentSocketID += 1
        socketID = self.__currentSocketID
        self.__lockSocketID.release()
        return socketID

    def __serve(self):
        if self.port is None:
            self.__serverSocket.bind((self.host, 0))
            self.port = self.__serverSocket.getsockname()[1]
        else:
            self.__serverSocket.bind((self.host, self.port))
        self.__serverSocket.listen()
        self.logger.info('[*] Serves at %s:%d over tcp.', self.host, self.port)
        while True:
            clientSocket, _ = self.__serverSocket.accept()

            socketID = self.__newSocketID()
            worker = Worker(
                socketID=socketID,
                socket_=clientSocket,
                receivingQueue=self.receivingQueue,
                sendingQueue=Queue(),
                io=self.__io
            )
            worker.link()


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
            io: IO = IO(),
            logLevel=logging.DEBUG):
        DataManagerClient.__init__(
            self,
            name=name,
            host=host,
            port=port,
            socket_=socket_,
            receivingQueue=receivingQueue,
            sendingQueue=sendingQueue,
            io=io,
            logLevel=logLevel
        )
        self.masterID = masterID


class TasksWorkerSide:

    def __init__(self, taskID: int, taskName: str):
        self.taskID = taskID
        self.taskName = taskName
        self.taskCalls = 0
        self.processedTime = 0
        self.processedCount = 0

    @abstractmethod
    def process(self, inputData):
        pass

    def recordProcessed(self, time_, calls):
        self.processedTime += time_
        self.taskCalls += calls
        self.processedCount += 1

    def averageCalls(self):
        if self.processedCount == 0:
            return 0
        return self.taskCalls / self.processedCount

    def averageProcessingTime(self):
        if self.processedCount == 0:
            return 0
        return self.processedTime / self.processedCount


class WorkerSysInfo(SystemInfo):

    def __init__(
            self,
            formatSize: bool
    ):
        super().__init__(formatSize)
        self.res.receivedTasksCount = 0,
        self.res.totalProcessingTime = 0.0,
        self.res.receivedDataSize = 0,
        self.res.sentDataSize = 0,
        self.res.changing += [
            'receivedTasksCount',
            'totalProcessingTime',
            'receivedDataSize',
            'sentDataSize',
        ]


class Broker:

    def __init__(
            self,
            masterIP: str,
            masterPort: int,
            thisIP: str,
            remoteLoggerHost: str = None,
            remoteLoggerPort: int = None,
            task: TasksWorkerSide = None,
            userID: int = None,
            appID: int = None,
            token: str = None,
            nextWorkerToken: str = None,
            ownedBy: int = None,
            userName: str = None,
            logLevel=logging.DEBUG):
        self.ownedBy: int = ownedBy
        self.task: TasksWorkerSide = task
        self.name: str = 'None'

        if self.ownedBy is None:
            self.name = 'Worker-Broker'
        else:
            self.name = 'Worker-%d-Task-%d-%s@%s' % (self.ownedBy, self.task.taskID, self.task.taskName, userName)
        self.logger = get_logger(self.name, logLevel)
        self.masterIP = masterIP
        self.masterPort = masterPort
        self.thisIP = thisIP
        self.remoteLoggerHost: str = remoteLoggerHost
        self.remoteLoggerPort: int = remoteLoggerPort
        self.token: str = token
        self.nextWorkerToken: str = nextWorkerToken
        self.userID: int = userID
        self.appID: int = appID
        self.workerID = None
        self.messageByAppID: dict[int, Queue] = defaultdict(Queue)
        self.__io = IO()

        self.master: Master = Master(
            name='%s@Master' % self.name,
            host=self.masterIP,
            port=self.masterPort,
            logLevel=self.logger.level,
            io=self.__io
        )
        self.nextWorker = None
        self.workers: List[Worker] = []

        self.service: DataManagerServer = DataManagerServer(
            host=self.thisIP,
            receivingQueue=self.master.receivingQueue,
            io=self.__io

        )
        self.thisPort = self.service.port
        self.__receivedTasksCount: int = 0
        self.__totalProcessingTime: float = 0
        self.sysInfo: WorkerSysInfo = WorkerSysInfo(
            formatSize=False
        )

    def __nodeLogger(self):
        sysInfo = self.sysInfo
        sleepTime = 10
        sysInfo.recordPerSeconds(seconds=sleepTime, nodeName=self.name)
        threading.Thread(
            target=self.__sendLogToRemoteLogger,
            args=(sysInfo,)
        ).start()
        while True:
            sysInfo.res.receivedTasksCount = self.__receivedTasksCount
            sysInfo.res.totalProcessingTime = self.__totalProcessingTime
            sysInfo.res.receivedDataSize = self.__io.receivedSize
            sysInfo.res.sentDataSize = self.__io.sentSize
            sleep(sleepTime)

    def __sendLog(self, message):
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.connect((self.remoteLoggerHost, self.remoteLoggerPort))

        messageEncrypted = Message.encrypt(message)
        serverSocket.sendall(struct.pack(">L", len(messageEncrypted)) + messageEncrypted)
        serverSocket.close()

    def __sendLogToRemoteLogger(self, sysInfo: WorkerSysInfo):
        if self.remoteLoggerHost is None \
                or self.remoteLoggerPort is None:
            return

        message = {
            'logList': sysInfo.res.keys(changing=False),
            'nodeName': self.name,
            'isChangingLog': False,
            'isTitle': True
        }
        self.__sendLog(message)
        message = {
            'logList': sysInfo.res.keys(changing=True),
            'nodeName': self.name,
            'isChangingLog': True,
            'isTitle': True
        }
        self.__sendLog(message)
        sleepTime = 10
        while True:
            sleep(sleepTime)
            message = {
                'logList': sysInfo.res.values(changing=True),
                'nodeName': self.name,
                'isChangingLog': True,
                'isTitle': False
            }
            self.__sendLog(message)

    def run(self):
        if self.task is not None:
            self.service.run()
            self.thisPort = self.service.port

        self.master.link()
        threading.Thread(target=self.__receivedMessageHandler).start()
        self.__register()
        threading.Thread(target=self.__nodeLogger).start()

        if self.task is not None:
            self.logger.info("Waiting for the next Worker")
            while len(self.nextWorkerToken) > 10 \
                    and self.nextWorker is None:
                pass
            self.logger.info("Connected to the next Worker")
            threading.Thread(
                target=self.__runApp,
                args=(self.task,)
            ).start()

    def __register(self) -> NoReturn:
        message = {'type': 'register',
                   'role': 'worker',
                   'ip': self.thisIP,
                   'port': self.thisPort,
                   'userID': self.userID,
                   'appID': self.appID,
                   'token': self.token,
                   'ownedBy': self.ownedBy,
                   'taskName': None if self.task is None else self.task.taskName,
                   'nodeSpecs': NodeSpecs(1, 2, 3, 4)}
        self.__sendTo(self.master, message)
        self.logger.info("[*] Registering ...")
        while self.workerID is None:
            pass
        self.name
        if self.nextWorkerToken is not None:
            message = {'type': 'lookup',
                       'token': self.nextWorkerToken}
            self.master.sendingQueue.put(Message.encrypt(message))
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
                userName = message['userName']
                appID = message['appID']
                token = message['token']
                nextWorkerToken = message['nextWorkerToken']
                ownedBy = self.workerID
                self.__runWorker(
                    userID=userID,
                    userName=userName,
                    appID=appID,
                    token=token,
                    nextWorkerToken=nextWorkerToken,
                    ownedBy=ownedBy
                )
            elif message['type'] == 'close':
                self.logger.warning(
                    'Master disconnected because %s',
                    message['reason'])
                os._exit(0)
            elif message['type'] == 'data':
                appID = message['appIDs'][0]
                self.messageByAppID[appID].put(message)

            elif message['type'] == 'workerInfo':
                nextWorkerIP = message['ip']
                nextWorkerPort = message['port']
                nextWorkerName = message['name']
                self.nextWorker = DataManagerClient(
                    name="%s@%s" % (self.name, nextWorkerName),
                    host=nextWorkerIP,
                    port=nextWorkerPort,
                    io=self.__io
                )
                self.nextWorker.link()
            elif message['type'] == 'nodeCurrentInfo':
                message = {
                    'type': 'workerCurrentInfo',
                    'workerID': self.workerID,
                    'titles': self.sysInfo.res.keys(),
                    'values': self.sysInfo.res.values()
                }
                self.master.sendingQueue.put(Message.encrypt(message))

    @staticmethod
    def __runWorker(
            userID: int,
            userName: str,
            appID: int,
            token: str,
            nextWorkerToken: str,
            ownedBy: int):
        threading.Thread(
            target=os.system,
            args=("python worker.py %d %d %s %s %d %s" % (
                userID,
                appID,
                token,
                nextWorkerToken,
                ownedBy,
                userName),)
        ).start()
        # os.system("python worker.py %d %d %s %s %d %s" % (userID, appID, token, nextWorkerToken, ownedBy, userName))

    def __runApp(self, app: TasksWorkerSide):
        self.logger.info('[*] AppID-%d-{%s} is serving ...', app.taskID, app.taskName)

        while True:
            message = self.messageByAppID[app.taskID].get()
            self.__receivedTasksCount += 1
            profiler = cProfile.Profile()
            profiler.enable()
            self.__executeApp(app, message)
            profiler.disable()
            profilerStats = pstats.Stats(profiler).sort_stats('ncalls')
            self.task.recordProcessed(profilerStats.total_tt, profilerStats.total_calls)
            self.recordComputingWeight()

    def recordComputingWeight(self):
        logPath = './log'
        if not os.path.exists(logPath):
            os.mkdir(logPath)
        filename = '%s/computingWeight@%s.csv' % (logPath, self.name)
        fileContent = 'averageProcessingTime, averageCalls, CPUFrequency\r\n' \
                      '%f, %f, %f\r\n' % (
                          self.task.averageProcessingTime(),
                          self.task.averageCalls(),
                          self.sysInfo.res.currentCPUFrequency
                      )
        self.writeFile(filename, fileContent)

    @staticmethod
    def writeFile(name, content):
        f = open(name, 'w')
        f.write(content)
        f.close()

    def __executeApp(self, task: TasksWorkerSide, message) -> NoReturn:
        startTime = time()
        self.logger.debug('Executing %s ...', task.taskName)
        data = message['data']
        result = task.process(data)
        if result is None:
            return

        message['workerID'] = self.workerID
        message['appID'] = task.taskID
        message['appIDs'] = message['appIDs'][1:]

        t = time() - message['time'][0]
        message['time'].append(t)

        if self.nextWorker is not None:
            message['type'] = 'data'
            message['data'] = result
            message['info'] = 'forward'
            self.__sendTo(self.nextWorker, message)
            self.logger.debug('Executed %s and send to next Worker', task.taskName)
        else:
            message['type'] = 'submitResult'

            del message['data']
            message['result'] = result
            self.__sendTo(self.master, message)
            self.logger.debug('Executed %s and returned the result', task.taskName)

        self.__totalProcessingTime += time() - startTime


if __name__ == '__main__':
    from apps import TestApp

    apps = [TestApp(appID=42)]
    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        thisIP='127.0.0.1',
        logLevel=logging.DEBUG)
    broker.run()
