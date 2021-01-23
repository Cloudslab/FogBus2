import logging
import sys
from apps import *
from node import Node
from connection import Message, Average
from exceptions import *
from logger import get_logger
from time import time
from typing import List


class ResponseTime:

    def __init__(self):
        self.__maxRecordNumber = 100
        self.__sentTimeTable: List[float] = [0 for _ in range(self.__maxRecordNumber)]


class User(Node):

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
            appName,
            label,
            logLevel=logging.DEBUG):

        self.isRegistered: threading.Event = threading.Event()
        self.appName = appName
        self.label = label
        self.app: ApplicationUserSide = None

        self.__lastDataSentTime = time()
        self.respondTime: Average = Average()
        super().__init__(
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[
                (self.__uploadAverageRespondTime, 10)],
            logLevel=logLevel
        )

    def run(self):
        self.__register()

    def __register(self):
        message = {
            'type': 'register',
            'role': 'user',
            'label': self.label,
            'appName': self.appName}
        self.sendMessage(message, self.masterAddr)
        self.isRegistered.wait()
        self.logger.info("Registered.")

    def handleMessage(self, message: Message):
        if message.type == 'registered':
            self.__handleRegistered(message)
        elif message.type == 'ready':
            self.__handleReady(message)
        elif message.type == 'result':
            self.__handleResult(message)

    def __handleRegistered(self, message: Message):
        role = message.content['role']
        if not role == 'user':
            raise RegisteredAsWrongRole
        self.id = message.content['id']
        self.name = message.content['name']
        self.gotName.set()
        self.role = role
        self.logger = get_logger(self.name, self.logLevel)
        self.isRegistered.set()

    def __handleReady(self, message: Message):
        threading.Thread(target=self.__ready).start()

    def __ready(self):
        self.logger.info("Resources is ready.")
        videoPath = sys.argv[8] if len(sys.argv) > 8 else None
        if self.appName == 'FaceDetection':
            self.app = FaceDetection(
                videoPath=videoPath,
                targetWidth=int(self.label))
        elif self.appName == 'FaceAndEyeDetection':
            self.app = FaceAndEyeDetection(
                videoPath=videoPath,
                targetWidth=int(self.label))
        elif self.appName == 'ColorTracking':
            self.app = ColorTracking(
                videoPath=videoPath,
                targetWidth=int(self.label))
        elif self.appName == 'VideoOCR':
            self.app = VideoOCR(
                videoPath=videoPath,
                targetWidth=int(self.label))
        if self.app is None:
            self.logger.info('Application does not exist.')
            os.killpg(os.getpgrp(), signal.SIGINT)
        self.logger.info('Running ...')
        self.app.run()

        while True:
            data = self.app.dataToSubmit.get()
            message = {
                'type': 'data',
                'userID': self.id,
                'data': data}
            self.sendMessage(message, self.masterAddr)
            self.__lastDataSentTime = time()

    def __handleResult(self, message: Message):
        result = message.content['result']
        self.respondTime.update((time() - self.__lastDataSentTime) * 1000)
        self.app.result.put(result)

    def __uploadAverageRespondTime(self):
        if self.respondTime.average() is None:
            return
        msg = {
            'type': 'respondTime',
            'respondTime': self.respondTime.average()}
        self.sendMessage(msg, self.loggerAddr)


if __name__ == "__main__":
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
    appName = sys.argv[6]
    label = sys.argv[7]
    user_ = User(
        myAddr=myAddr_,
        masterAddr=masterAddr_,
        loggerAddr=loggerAddr_,
        appName=appName,
        label=label,
    )
    user_.run()
