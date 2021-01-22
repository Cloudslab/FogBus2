import threading
import logging
import os
import signal

from queue import Queue
from connection import Server, Message, Connection, Source, RoundTripDelay, ReceivedPackageSize
from abc import abstractmethod
from typing import Dict, Tuple, DefaultDict
from logging import Logger
from time import time
from collections import defaultdict


class Node:

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
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
        self.roundTripDelay: Dict[str, RoundTripDelay] = {}
        self.receivedPackageSize: Dict[str, ReceivedPackageSize] = {}

    @abstractmethod
    def run(self):
        pass

    def __messageHandler(self):
        while True:
            message, messageSize = self.receivedMessage.get()

            if message.source.name not in self.receivedPackageSize:
                receivedPackageSize = ReceivedPackageSize(
                    name=message.source.name,
                    role=message.source.role,
                    id_=message.source.id
                )
                self.receivedPackageSize[message.source.name] = receivedPackageSize
            self.receivedPackageSize[message.source.name].received(messageSize)

            if message.type == 'ping':
                self.__handleRoundTripDelay(message)
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
        if not self.role == 'master':
            message = {'type': 'exit'}
            self.sendMessage(message, self.masterAddr)
        print('[*] Bye.')
        os._exit(0)

    def handleSignal(self):
        signal.signal(signal.SIGINT, self.__signalHandler)

    def __handleRoundTripDelay(self, message: Message):
        delay = time() - message.content['time']
        source = message.source
        if source.name not in self.roundTripDelay:
            roundTripDelay = RoundTripDelay(
                name=source.name,
                role=source.role,
                id_=source.id,
                delay=delay
            )
            self.roundTripDelay[source.name] = roundTripDelay
            return
        self.roundTripDelay[source.name].update(delay)
