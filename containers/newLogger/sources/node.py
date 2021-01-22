import threading
import logging
import os
import signal
import traceback
from socket import error as SocketError
from queue import Queue
from connection import Server, Message, Connection, Source, Average
from abc import abstractmethod
from typing import Dict, Tuple, List, Callable
from logging import Logger
from time import time, sleep
from resourcesInfo import Resources

Address = Tuple[str, int]


class Node:

    def __init__(
            self,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            periodicTasks=None,
            logLevel=logging.DEBUG):
        self.name: str = None
        self.role: str = None
        self.id: int = None
        self.myAddr = myAddr
        self.masterAddr = masterAddr
        self.loggerAddr = loggerAddr
        self.receivedMessage: Queue[Tuple[Message, int]] = Queue()
        self.isRegistered: threading.Event = threading.Event()
        self.__myService = Server(
            self.myAddr,
            self.receivedMessage,
        )
        threading.Thread(target=self.__messageHandler).start()
        self.logLevel = logLevel
        self.logger: Logger = None
        self.handleSignal()
        # Node stats
        self.roundTripDelay: Dict[str, Average] = {}
        self.receivedPackageSize: Dict[str, Average] = {}
        self.resources: Resources = Resources()

        defaultPeriodicTasks = [
            self.__uploadResources,
            self.__uploadAverageReceivedPackageSize,
            self.__uploadRoundTripDelay,
        ]
        if periodicTasks is None:
            periodicTasks = []
        self.periodicTasks: List[Callable] = defaultPeriodicTasks + periodicTasks
        for runner in self.periodicTasks:
            threading.Thread(
                target=self.__periodic,
                args=(runner,)
            ).start()

    @abstractmethod
    def run(self):
        pass

    def __messageHandler(self):
        while True:
            message, messageSize = self.receivedMessage.get()

            if message.source.name not in self.receivedPackageSize:
                receivedPackageSize = Average(
                    name=message.source.name,
                    role=message.source.role,
                    id_=message.source.id
                )
                self.receivedPackageSize[message.source.name] = receivedPackageSize
            self.receivedPackageSize[message.source.name].update(messageSize)

            if message.type == 'ping':
                self.__handleRoundTripDelay(message)
                continue
            elif message.type == 'resourcesQuery':
                self.__handleResourcesQuery(message)
                continue
            self.handleMessage(message)

    def sendMessage(self, message: Dict, addr):
        source = Source(
            addr=self.myAddr,
            role=self.role,
            id_=self.id,
            name=self.name
        )
        message['source'] = source
        Connection(addr).send(message)

        ping = {'type': 'ping', 'time': time(), 'source': source}
        Connection(addr).send(ping)

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
        if self.role not in {'master', 'remoteLogger'}:
            message = {'type': 'exit'}
            self.sendMessage(message, self.masterAddr)
        self.__myService.serverSocket.close()
        print('[*] Bye.')
        os._exit(0)

    def handleSignal(self):
        signal.signal(signal.SIGINT, self.__signalHandler)

    def __handleRoundTripDelay(self, message: Message):
        delay = time() - message.content['time']
        source = message.source
        if source.name not in self.roundTripDelay:
            roundTripDelay = Average(
                name=source.name,
                role=source.role,
                id_=source.id
            )
            self.roundTripDelay[source.name] = roundTripDelay
            return
        self.roundTripDelay[source.name].update(delay * 1000)

    def __handleResourcesQuery(self, message: Message):
        if not message.source.addr == self.masterAddr:
            return
        msg = {'type': 'nodeResources', 'resources': self.resources.all()}
        self.sendMessage(msg, message.source.addr)

    def __periodic(self, runner: Callable):
        lastCollectTime = time()
        while True:
            timeToSleep = lastCollectTime + 10 - time()
            sleep(0 if timeToSleep < 0 else timeToSleep)
            if self.role is None:
                continue
            lastCollectTime = time()
            runner()

    def __uploadResources(self):
        msg = {'type': 'nodeResources', 'resources': self.resources.all()}
        self.sendMessage(msg, self.loggerAddr)

    def __uploadAverageReceivedPackageSize(self):
        msg = {
            'type': 'averageReceivedPackageSize',
            'averageReceivedPackageSize': self.receivedPackageSize}
        self.sendMessage(msg, self.loggerAddr)

    def __uploadRoundTripDelay(self):
        msg = {
            'type': 'roundTripDelay',
            'roundTripDelay': self.roundTripDelay}
        self.sendMessage(msg, self.loggerAddr)
