import threading
import pickle
import traceback
import logging

from queue import Queue
from connection import Server, Message, Connection
from abc import abstractmethod
from typing import Dict
from logging import Logger


def encrypt(obj) -> bytes:
    data = pickle.dumps(obj, 0)
    return data


def decrypt(msg: bytes) -> Dict:
    try:
        obj = pickle.loads(msg, fix_imports=True, encoding="bytes")
        return obj
    except Exception:
        traceback.print_exc()


class Node:

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
            logLevel=logging.DEBUG):
        self.name: str = None
        self.role: str = None
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

    def sendMessage(self, message: Dict, addr):
        print(message)
        message['addr'] = self.myAddr
        encryptMessage = encrypt(message)
        Connection(addr).send(encryptMessage)

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
