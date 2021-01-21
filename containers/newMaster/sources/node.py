import threading
import logging

from queue import Queue
from connection import Server, Message, Connection, Source
from abc import abstractmethod
from typing import Dict, Tuple
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

    @abstractmethod
    def run(self):
        pass

    def __messageHandler(self):
        while True:
            message = self.receivedMessage.get()
            self.handleMessage(message)

    def sendMessage(self, message: Dict, addr: Tuple[str, int]):
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
