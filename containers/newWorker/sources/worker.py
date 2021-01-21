import sys
import logging
import threading
import os
import re
from exceptions import *
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
        elif self.isMessage(message, 'runTaskHandler'):
            self.__handleRunTaskHandler(message)

    def __handleRegistered(self, message: Message):
        role = message.content['role']
        if not role == 'worker':
            raise RegisteredAsWrongRole
        self.workerID = message.content['id']
        self.name = message.content['name']
        self.logger = get_logger(self.name, self.logLevel)
        self.isRegistered.set()

    @staticmethod
    def camel_to_snake(name):
        # https://stackoverflow.com/questions/1175208
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def __handleRunTaskHandler(self, message: Message):

        userID = message.content['userID']
        userName = message.content['userName']
        taskName = message.content['taskName']
        token = message.content['token']
        childTaskTokens = message.content['childTaskTokens']
        runningOnWorker = self.workerID
        # threading.Thread(
        #     target=os.system,
        #     args=(
        #         "cd tasks/%s && docker-compose run %s %s %s %d %s %d "
        #         "%d %s %s %s %d %s" % (
        #             taskName,
        #             self.camel_to_snake(taskName),
        #             self.myAddr[0],
        #             self.masterAddr[0],
        #             self.masterAddr[1],
        #             self.loggerAddr[0],
        #             self.loggerAddr[1],
        #             userID,
        #             taskName,
        #             token,
        #             ','.join(childTaskTokens) if len(childTaskTokens) else 'None',
        #             ownedBy,
        #             userName),)
        # ).start()

        # threading.Thread(
        #     target=os.system,
        #     args=(
        #         "cd taskSample && python taskHandler.py %s %s %d %s %d "
        #         "%d %s %s %s %s %d" % (
        #             self.myAddr[0],
        #             self.masterAddr[0],
        #             self.masterAddr[1],
        #             self.loggerAddr[0],
        #             self.loggerAddr[1],
        #             userID,
        #             userName,
        #             taskName,
        #             token,
        #             ','.join(childTaskTokens) if len(childTaskTokens) else 'None',
        #             runningOnWorker
        #         ),)
        # ).start()

        import socket
        tmpSocket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM)
        tmpSocket.bind(('', 0))
        port = tmpSocket.getsockname()[1]
        tmpSocket.close()
        myAddr_ = (self.myAddr[0], port)
        from taskSample.taskHandler import TaskHandler
        taskHandler_ = TaskHandler(
            myAddr=myAddr_,
            masterAddr=self.masterAddr,
            loggerAddr=self.loggerAddr,
            userID=userID,
            userName=userName,
            taskName=taskName,
            token=token,
            childTaskTokens=childTaskTokens,
            runningOnWorker=runningOnWorker
        )
        taskHandler_.run()


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
