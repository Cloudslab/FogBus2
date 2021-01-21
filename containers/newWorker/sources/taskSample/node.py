import threading
import logging
import os
import signal

from queue import Queue
from connection import Server, Message, Connection, Source
from abc import abstractmethod
from typing import Dict
from logging import Logger


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
        self.receivedMessage: Queue[Message] = Queue()
        self.isRegistered: threading.Event = threading.Event()
        self.__myService = Server(
            self.myAddr,
            self.receivedMessage
        )
        threading.Thread(target=self.__messageHandler).start()
        self.logLevel = logLevel
        self.logger: Logger = None
        self.handleSignal()

    @abstractmethod
    def run(self):
        pass

    def __messageHandler(self):
        while True:
            message = self.receivedMessage.get()
            self.handleMessage(message)

    def sendMessage(self, message: Dict, addr):
        message['source'] = Source(
            addr=self.myAddr,
            role=self.role,
            id_=self.id
        )
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
        if not self.role == 'master':
            message = {'type': 'exit'}
            self.sendMessage(message, self.masterAddr)
        print('[*] Bye.')
        os._exit(0)

    def handleSignal(self):
        signal.signal(signal.SIGINT, self.__signalHandler)
