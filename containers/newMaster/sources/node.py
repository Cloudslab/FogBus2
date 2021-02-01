import threading
import logging
import os
import signal
from queue import Queue
from connection import Server, Message, Connection, Source, Median, Identity
from abc import abstractmethod
from typing import Dict, Tuple, List, Callable
from logging import Logger
from time import time, sleep
from resourcesInfo import Resources

Address = Tuple[str, int]
PeriodicTask = Tuple[Callable, float]


class Node(Server, Resources):

    def __init__(
            self,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            coresCount=None,
            cpuFrequency=None,
            memory=None,
            periodicTasks: List[PeriodicTask] = None,
            threadNumber: int = 32,
            ignoreSocketErr: bool = False,
            logLevel=logging.DEBUG):
        self.myAddr = myAddr
        self.masterAddr = masterAddr
        self.loggerAddr = loggerAddr
        self.coresCount = coresCount
        self.cpuFrequency = cpuFrequency
        self.memorySize = memory
        self.ignoreSocketErr = ignoreSocketErr
        self.me = Identity(
            nameLogPrinting='Me',
            addr=self.myAddr,
        )
        self.master = Identity(
            nameLogPrinting='Master',
            addr=self.masterAddr,
        )
        self.remoteLogger = Identity(
            nameLogPrinting='RemoteLogger',
            addr=self.loggerAddr,
        )

        Resources.__init__(
            self,
            addr=self.myAddr,
            coresCount=self.coresCount,
            cpuFrequency=self.cpuFrequency,
            memory=self.memorySize
        )
        self.name: str = None
        self.nameLogPrinting: str = None
        self.nameConsistent: str = None
        self.__gotName: threading.Event = threading.Event()
        self.role: str = None
        self.id: int = None
        self.machineID: str = self.uniqueID()

        self.receivedMessage: Queue[Tuple[Message, int]] = Queue()
        self.messageToSend: Queue[Tuple[Dict, Tuple[str, int]]] = Queue()
        self.isRegistered: threading.Event = threading.Event()
        Server.__init__(
            self,
            addr=self.myAddr,
            messagesQueue=self.receivedMessage,
            threadNumber=threadNumber // 4)
        self.myAddr = self.addr
        for i in range(threadNumber):
            threading.Thread(
                target=self.__messageHandler,
                name="HandlingMessage-%d" % i
            ).start()
            threading.Thread(
                target=self.__messageSender,
                name="MessageSender-%d" % i
            ).start()
        self.logLevel = logLevel
        self.logger: Logger = None
        self.handleSignal()
        # Node stats
        self.lock = threading.Lock()
        self.receivedPackageSize: Dict[str, Median] = {}
        self.delays: Dict[str, Median] = {}
        self.networkTimeDiff: Dict[Tuple[str, int], float] = {}

        defaultPeriodicTasks: List[PeriodicTask] = [
            (self.__uploadResources, 10)]
        if not self.role == 'RemoteLogger':
            defaultPeriodicTasks += [
                (self.__uploadMedianReceivedPackageSize, 10),
                (self.__uploadDelays, 10)]
        if periodicTasks is None:
            periodicTasks = []
        self.periodicTasks: List[PeriodicTask] = defaultPeriodicTasks + periodicTasks
        for runner, period in self.periodicTasks:
            threading.Thread(
                target=self.__periodic,
                args=(runner, period)
            ).start()

    def setName(self, message: Message = None):
        if self.role in {'Master', 'RemoteLogger'}:
            self.name = '%s' % self.role
            self.nameLogPrinting = '%s-%d' % (self.name, self.id)
            self.nameConsistent = '%s#%s' % (self.name, self.machineID)
        else:
            self.name = message.content['name']
            self.nameLogPrinting = message.content['nameLogPrinting']
            self.nameConsistent = message.content['nameConsistent']
        self.__gotName.set()

    @abstractmethod
    def run(self):
        pass

    def __messageSender(self):
        while True:
            message, addr = self.messageToSend.get()
            try:
                Connection(addr).send(message)
            except OSError:
                if self.ignoreSocketErr:
                    continue
                if addr == self.master.addr:
                    warning = 'Cannot connect to the system. Exit.'
                    if self.logger is None:
                        print(warning)
                    else:
                        self.logger.warning(warning)
                    os._exit(-1)
                msg = {'type': 'exit', 'reason': 'Network Error.'}
                self.sendMessage(msg, self.master.addr)

    def __messageHandler(self):
        while True:
            message, messageSize = self.receivedMessage.get()
            _receivedAt = time() * 1000
            message.content['delay'] = _receivedAt - message.content['_sentAt']
            message.content['_receivedAt'] = _receivedAt
            if message.type == 'respondTimeDiff':
                self.__handleRespondTimeDiff(message)
                continue
            elif message.type == 'resourcesQuery':
                self.__handleResourcesQuery(message)
                continue
            elif message.type == 'stop':
                self.__handleStop(message)
                continue
            if message.source.addr in self.networkTimeDiff:
                message.content['delay'] += self.networkTimeDiff[message.source.addr]
            self.__statMedianPackageSize(message, messageSize)
            self.handleMessage(message)
            self.__respondTimeDiff(message)

    def __statMedianPackageSize(self, message: Message, messageSize: int):
        if not message.source.nameConsistent == self.nameConsistent:
            self.lock.acquire()
            if message.source.name not in self.receivedPackageSize:
                receivedPackageSize = Median(
                    addr=message.source.addr,
                    name=message.source.name,
                    nameLogPrinting=message.source.nameLogPrinting,
                    nameConsistent=message.source.nameConsistent,
                    role=message.source.role,
                    id_=message.source.id,
                    machineID=message.source.machineID)
                self.receivedPackageSize[message.source.name] = receivedPackageSize
            self.receivedPackageSize[message.source.name].update(messageSize)
            self.lock.release()

    def __respondTimeDiff(self, message: Message):
        msg = {
            'type': 'respondTimeDiff',
            'A': message.content['_sentAt'],
            'X': message.content['_receivedAt']}
        self.sendMessage(msg, message.source.addr)

    def __handleRespondTimeDiff(self, message: Message):
        A = message.content['A']
        X = message.content['X']
        Y = message.content['_sentAt']
        B = message.content['_receivedAt']
        # delay = (B - A - Y + X) / 2
        delayAtMost = B - A - Y + X
        self.lock.acquire()
        if message.source.machineID not in self.delays:
            medianDelay = Median(
                addr=message.source.addr,
                name=message.source.name,
                nameLogPrinting=message.source.nameLogPrinting,
                nameConsistent=message.source.nameConsistent,
                role=message.source.role,
                id_=message.source.id,
                machineID=message.source.machineID)
            self.delays[message.source.machineID] = medianDelay
        self.delays[message.source.machineID].update(delayAtMost)
        self.lock.release()

    def sendMessage(self, message: Dict, addr: Address):
        source = Source(
            role=self.role,
            id_=self.id,
            addr=self.myAddr,
            name=self.name,
            nameLogPrinting=self.nameLogPrinting,
            nameConsistent=self.nameConsistent,
            machineID=self.machineID
        )
        message['source'] = source
        self.messageToSend.put((message, addr))

    @abstractmethod
    def handleMessage(self, message: Message):
        pass

    @staticmethod
    def isMessage(message: Message, name: str):
        if 'type' not in message.content:
            return False
        if not message.content['type'] == name:
            return False
        return True

    def __signalHandler(self, sig, frame):
        # https://stackoverflow.com/questions/1112343
        print('[*] Exiting ...')
        if self.role not in {'Master', 'RemoteLogger'}:
            message = {'type': 'exit', 'reason': 'Manually interrupted.'}
            self.sendMessage(message, self.master.addr)
            return
        os._exit(0)

    def handleSignal(self):
        signal.signal(signal.SIGINT, self.__signalHandler)
        signal.signal(signal.SIGTERM, self.__signalHandler)

    def __handleResourcesQuery(self, message: Message):
        if not message.source.addr == self.masterAddr:
            return
        msg = {'type': 'nodeResources', 'resources': self.allResources()}
        self.sendMessage(msg, message.source.addr)

    def __handleStop(self, message: Message):
        reasonFormatted = '%s asks me to stop. ' \
                          'Reason: %s' % (
                              message.source.nameLogPrinting,
                              message.content['reason'])
        if self.logger is not None:
            self.logger.warning(reasonFormatted)
            self.logger.info('Exit.')
        else:
            print(reasonFormatted)
        os._exit(0)

    def __periodic(self, runner: Callable, period: float):
        self.__gotName.wait()
        runner()
        lastCollectTime = time()
        while True:
            timeToSleep = lastCollectTime + period - time()
            sleep(0 if timeToSleep < 0 else timeToSleep)
            if self.role is None:
                continue
            lastCollectTime = time()
            runner()

    def __uploadResources(self):
        msg = {'type': 'nodeResources', 'resources': self.allResources()}
        self.sendMessage(msg, self.remoteLogger.addr)

    def __uploadMedianReceivedPackageSize(self):
        self.lock.acquire()
        allMedian = {}
        for k, median in self.receivedPackageSize.items():
            if k is None:
                continue
            allMedian[k] = median.median()
        msg = {
            'type': 'medianReceivedPackageSize',
            'medianReceivedPackageSize': allMedian}
        self.sendMessage(msg, self.remoteLogger.addr)
        self.lock.release()

    def __uploadDelays(self):
        self.lock.acquire()
        allDelay = {}
        for k, median in self.delays.items():
            if k is None:
                continue
            allDelay[k] = median.median()
        msg = {
            'type': 'delays',
            'delays': allDelay}
        self.sendMessage(msg, self.remoteLogger.addr)
        self.lock.release()
