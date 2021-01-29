import threading
import logging
import os
import signal
from queue import PriorityQueue
from connection import Server, Message, Connection, Source, Average, Identity
from abc import abstractmethod
from typing import Dict, Tuple, List, Callable
from logging import Logger
from time import time, sleep
from resourcesInfo import Resources

Address = Tuple[str, int]
PeriodicTask = Tuple[Callable, float]


class Node:

    def __init__(
            self,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            periodicTasks: List[PeriodicTask] = None,
            threadNumber: int = 128,
            logLevel=logging.DEBUG):
        self.myAddr = myAddr
        self.masterAddr = masterAddr
        self.loggerAddr = loggerAddr
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
        self.resources: Resources = Resources(
            addr=self.myAddr)
        self.name: str = None
        self.nameLogPrinting: str = None
        self.nameConsistent: str = None
        self.__gotName: threading.Event = threading.Event()
        self.role: str = None
        self.id: int = None
        self.machineID: str = self.resources.uniqueID()

        self.receivedMessage: PriorityQueue[Tuple[Message, int]] = PriorityQueue()
        self.isRegistered: threading.Event = threading.Event()
        self.__myService = Server(
            self.myAddr,
            self.receivedMessage,
            threadNumber=threadNumber // 4)
        for i in range(threadNumber):
            t = threading.Thread(
                target=self.__messageHandler,
                name="HandlingMessage-%d" % i
            )
            t.start()
        self.logLevel = logLevel
        self.logger: Logger = None
        self.handleSignal()
        # Node stats
        self.receivedPackageSize: Dict[str, Average] = {}
        self.delays: Dict[str, Average] = {}

        defaultPeriodicTasks: List[PeriodicTask] = [
            (self.__uploadResources, 10)]
        if not self.role == 'RemoteLogger':
            defaultPeriodicTasks += [
                (self.__uploadAverageReceivedPackageSize, 10),
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

    def __messageHandler(self):
        while True:
            message, messageSize = self.receivedMessage.get()
            _receivedAt = time() * 1000
            message.content['delay'] = _receivedAt - message.content['_sentAt']
            message.content['_receivedAt'] = _receivedAt

            if not message.source.nameConsistent == self.nameConsistent:
                if message.source.name not in self.receivedPackageSize:
                    receivedPackageSize = Average(
                        addr=message.source.addr,
                        name=message.source.name,
                        nameLogPrinting=message.source.nameLogPrinting,
                        nameConsistent=message.source.nameConsistent,
                        role=message.source.role,
                        id_=message.source.id,
                        machineID=message.source.machineID
                    )
                    self.receivedPackageSize[message.source.name] = receivedPackageSize
                self.receivedPackageSize[message.source.name].update(messageSize)
                if message.source.name not in self.delays:
                    delay = Average(
                        addr=message.source.addr,
                        name=message.source.name,
                        nameLogPrinting=message.source.nameLogPrinting,
                        nameConsistent=message.source.nameConsistent,
                        role=message.source.role,
                        id_=message.source.id,
                        machineID=message.source.machineID
                    )
                    self.delays[message.source.name] = delay
                self.delays[message.source.name].update(message.content['delay'])

            elif message.type == 'resourcesQuery':
                self.__handleResourcesQuery(message)
                continue
            elif message.type == 'stop':
                self.__handleStop(message)
                continue
            self.handleMessage(message)

    def sendMessage(self, message: Dict, identity: Identity):
        try:
            self._sendMessage(message, identity.addr)
        except OSError:
            if identity.addr == self.master.addr:
                warning = 'Cannot connect to the system. Exit.'
                if self.logger is None:
                    print(warning)
                else:
                    self.logger.warning(warning)
                os._exit(-1)
            msg = {'type': 'exit', 'reason': 'Network Error.'}
            self.sendMessage(msg, identity)

    def sendMessageIgnoreErr(self, message: Dict, identity: Identity):
        try:
            self._sendMessage(message, identity.addr)
        except OSError:
            pass

    def _sendMessage(self, message: Dict, addr: Tuple[str, int]):
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
        Connection(addr).send(message)

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
        if self.role not in {'Master', 'RemoteLogger'}:
            message = {'type': 'exit', 'reason': 'Manually interrupted.'}
            self.sendMessage(message, self.master)
        self.__myService.serverSocket.close()
        print('[*] Bye.')
        os._exit(0)

    def handleSignal(self):
        signal.signal(signal.SIGINT, self.__signalHandler)

    def __handleResourcesQuery(self, message: Message):
        if not message.source.addr == self.masterAddr:
            return
        msg = {'type': 'nodeResources', 'resources': self.resources.all()}
        self.sendMessage(msg, message.source)

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
        msg = {'type': 'nodeResources', 'resources': self.resources.all()}
        self.sendMessage(msg, self.remoteLogger)

    def __uploadAverageReceivedPackageSize(self):
        msg = {
            'type': 'averageReceivedPackageSize',
            'averageReceivedPackageSize': self.receivedPackageSize}
        self.sendMessage(msg, self.remoteLogger)

    def __uploadDelays(self):
        msg = {
            'type': 'delays',
            'delays': self.delays}
        self.sendMessage(msg, self.remoteLogger)
