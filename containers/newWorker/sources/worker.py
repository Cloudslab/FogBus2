import sys
import logging
import threading
from apps import *
from exceptions import *
from datatype import Broker
from connection import Connection, Message
from queue import Queue
from node import Node
from logger import get_logger
from logging import Logger


class Worker(Node):

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
            logLevel=logging.DEBUG):
        super().__init__(
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            logLevel=logLevel
        )

        self.isRegistered: threading.Event = threading.Event()
        self.workerID: int = None

    def run(self):
        self.__register()

    def __register(self):
        message = {'type': 'register',
                   'role': 'worker'}
        self.sendMessage(message, self.masterAddr)
        self.isRegistered.wait()
        self.logger.info("Registered.")

    def handleMessage(self, message: Message):
        if self.isMessage(message, 'registered'):
            self.__handleRegistered(message)

    def __handleRegistered(self, message: Message):
        role = message.content['role']
        if not role == 'worker':
            raise RegisteredAsWrongRole
        self.workerID = message.content['id']
        self.name = message.content['name']
        self.isRegistered.set()
        self.logger = get_logger(self.name, self.logLevel)


if __name__ == '__main__':
    myAddr_ = (sys.argv[1], int(sys.argv[2]))
    masterAddr_ = (sys.argv[3], int(sys.argv[4]))
    loggerAddr_ = (sys.argv[5], int(sys.argv[6]))
    worker_ = Worker(
        myAddr=myAddr_,
        masterAddr=masterAddr_,
        loggerAddr=loggerAddr_
    )
    worker_.run()
