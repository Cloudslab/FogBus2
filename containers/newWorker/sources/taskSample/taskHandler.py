import sys
import logging
import threading
import os
from exceptions import *
from connection import Connection, Message
from queue import Queue
from node import Node
from logger import get_logger
from logging import Logger
from typing import List, Dict
from collections import defaultdict
from time import sleep, time
from apps import *


class ProcessingTime:

    def __init__(self):
        self.__maxRecordNum = 100
        self.__index = 0
        self.__costTable: List[float] = [0 for _ in range(self.__maxRecordNum)]

    def update(self, cost_):
        self.__costTable[self.__index] = cost_
        self.__index = (self.__index + 1) % self.__maxRecordNum

    def average(self):
        total, count = 0, 0
        for cost in self.__costTable:
            if cost == 0:
                break
            total += cost
            count += 1
        if count == 0:
            return None
        return 1000 * total / count


class TaskHandler(Node):

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
            userID: int,
            userName: str,
            taskName: str,
            token: str,
            childTaskTokens: List[str],
            runningOnWorker: int,
            logLevel=logging.DEBUG):
        super().__init__(
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[self.__processTime],
            logLevel=logLevel
        )

        self.userID: int = userID
        self.userName: str = userName
        self.taskName: str = taskName
        self.token: str = token
        self.childTaskTokens: List[str] = childTaskTokens
        self.runningOnWorker: int = runningOnWorker
        self.isRegistered: threading.Event = threading.Event()
        self.childrenAddr: Dict[str, tuple] = {}
        self.processTime: ProcessingTime = ProcessingTime()

        app = None
        if taskName == 'FaceDetection':
            app = FaceDetection()
        elif taskName == 'EyeDetection':
            app = EyeDetection()
        elif taskName == 'ColorTracking':
            app = ColorTracking()
        elif taskName == 'BlurAndPHash':
            app = BlurAndPHash()
        elif taskName == 'OCR':
            app = OCR()
        if app is None:
            os._exit(0)
        self.app: TasksWorkerSide = app

    def __processTime(self):
        msg = {
            'type': 'averageProcessTime',
            'averageProcessTime': self.processTime.average()}
        self.sendMessage(msg, self.loggerAddr)

    def run(self):
        self.__register()
        self.__lookupChildren()

    def __register(self):
        message = {
            'type': 'register',
            'role': 'taskHandler',
            'userID': self.userID,
            'taskName': self.taskName,
            'runningOnWorker': self.runningOnWorker,
            'token': self.token}
        self.sendMessage(message, self.masterAddr)
        self.isRegistered.wait()
        self.logger.info("Registered.")

    def __lookupChildren(self):
        while True:
            if len(self.childTaskTokens) == len(self.childrenAddr.keys()):
                break
            for childToken in self.childTaskTokens:
                if childToken in self.childrenAddr:
                    continue
                msg = {'type': 'lookup', 'token': childToken}
                self.sendMessage(msg, self.masterAddr)
            sleep(1)
        msg = {'type': 'ready', 'token': self.token}
        self.sendMessage(msg, self.masterAddr)
        self.logger.info('Got children\'s addr')

    def handleMessage(self, message: Message):
        if message.type == 'registered':
            self.__handleRegistered(message)
        elif message.type == 'taskHandlerInfo':
            self.__handleTaskHandlerInfo(message)
        elif message.type == 'data':
            self.__handleData(message)
        elif message.type == 'stop':
            self.__handleStop(message)

    def __handleRegistered(self, message: Message):
        role = message.content['role']
        if not role == 'taskHandler':
            raise RegisteredAsWrongRole
        self.id = message.content['id']
        self.name = message.content['name']
        self.role = role
        self.logger = get_logger(self.name, self.logLevel)
        self.isRegistered.set()

    def __handleTaskHandlerInfo(self, message: Message):
        taskHandlerAddr = message.content['addr']
        taskHandlerToken = message.content['token']
        if taskHandlerToken not in self.childTaskTokens:
            return
        self.childrenAddr[taskHandlerToken] = taskHandlerAddr

        if not len(self.childTaskTokens) == len(self.childrenAddr.keys()):
            return
        msg = {'type': 'ready', 'token': self.token}
        self.sendMessage(msg, self.masterAddr)

    def __handleData(self, message: Message):
        data = message.content['data']
        startTime = time()
        result = self.app.process(data)
        self.processTime.update(time() - startTime)
        if result is None:
            return

        msg = message.content
        if len(self.childrenAddr.keys()):
            msg['data'] = result
            for _, addr in self.childrenAddr.items():
                self.sendMessage(msg, addr)
            return

        del msg['data']
        msg['type'] = 'result'
        msg['result'] = result

        self.sendMessage(msg, self.masterAddr)

    def __handleStop(self, message: Message):
        msg = {'type': 'exit'}
        self.sendMessage(msg, self.masterAddr)
        self.logger.info('Exit.')
        os._exit(0)


if __name__ == '__main__':
    import socket

    tmpSocket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM)
    tmpSocket.bind(('', 0))
    port = tmpSocket.getsockname()[1]
    tmpSocket.close()
    myAddr_ = (sys.argv[1], port)
    masterAddr_ = (sys.argv[2], int(sys.argv[3]))
    loggerAddr_ = (sys.argv[4], int(sys.argv[5]))

    userID = int(sys.argv[6])
    userName = sys.argv[7]
    taskName = sys.argv[8]
    token = sys.argv[9]
    if sys.argv[10] == 'None':
        childTaskTokens = []
    else:
        childTaskTokens = sys.argv[10].split(',')
    runningOnWorker = int(sys.argv[11])

    taskHandler_ = TaskHandler(
        myAddr=myAddr_,
        masterAddr=masterAddr_,
        loggerAddr=loggerAddr_,
        userID=userID,
        userName=userName,
        taskName=taskName,
        token=token,
        childTaskTokens=childTaskTokens,
        runningOnWorker=runningOnWorker
    )
    taskHandler_.run()
