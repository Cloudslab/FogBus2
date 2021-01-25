import sys
import logging
import threading
import os
import signal
from exceptions import *
from connection import Message, Average
from node import Node
from logger import get_logger
from typing import List, Dict
from time import sleep, time
from apps import *


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
            workerID: int,
            logLevel=logging.DEBUG):

        self.userID: int = userID
        self.userName: str = userName
        self.taskName: str = taskName
        self.token: str = token
        self.childTaskTokens: List[str] = childTaskTokens
        self.workerID: int = workerID
        self.isRegistered: threading.Event = threading.Event()
        self.childrenAddr: Dict[str, tuple] = {}
        self.processTime: Average = Average()

        super().__init__(
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[
                (self.__uploadAverageProcessTime, 10)],
            logLevel=logLevel
        )

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
            os.killpg(os.getpgrp(), signal.SIGINT)
        self.app: TasksWorkerSide = app

    def __uploadAverageProcessTime(self):
        if self.processTime.average() is None:
            return
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
            'role': 'TaskHandler',
            'userID': self.userID,
            'taskName': self.taskName,
            'workerID': self.workerID,
            'token': self.token,
            'machineID': self.machineID}
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
        self.logger.info(self.childTaskTokens)

    def handleMessage(self, message: Message):
        if message.type == 'registered':
            self.__handleRegistered(message)
        elif message.type == 'taskHandlerInfo':
            self.__handleTaskHandlerInfo(message)
        elif message.type == 'data':
            self.__handleData(message)

    def __handleRegistered(self, message: Message):
        role = message.content['role']
        if not role == 'TaskHandler':
            raise RegisteredAsWrongRole
        self.id = message.content['id']
        self.role = role
        self.setName(message)
        self.logger = get_logger(self.nameLogPrinting, self.logLevel)
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
        self.processTime.update((time() - startTime) * 1000)
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

    userID_ = int(sys.argv[6])
    userName_ = sys.argv[7]
    taskName_ = sys.argv[8]
    token_ = sys.argv[9]
    if sys.argv[10] == 'None':
        childTaskTokens_ = []
    else:
        childTaskTokens_ = sys.argv[10].split(',')
    workerID_ = int(sys.argv[11])

    taskHandler_ = TaskHandler(
        myAddr=myAddr_,
        masterAddr=masterAddr_,
        loggerAddr=loggerAddr_,
        userID=userID_,
        userName=userName_,
        taskName=taskName_,
        token=token_,
        childTaskTokens=childTaskTokens_,
        workerID=workerID_
    )
    taskHandler_.run()
