import logging
import sys
import os
from apps import *
from node import Node
from connection import Message, Average
from exceptions import *
from logger import get_logger
from time import time
from typing import List, Tuple

Address = Tuple[str, int]


class ResponseTime:

    def __init__(self):
        self.__maxRecordNumber = 100
        self.__sentTimeTable: List[float] = [0 for _ in range(self.__maxRecordNumber)]


class User(Node):

    def __init__(
            self,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            appName: str,
            showWindow: bool,
            label: str,
            videoPath: str,
            logLevel=logging.DEBUG):
        Node.__init__(
            self,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[
                (self.__uploadAverageRespondTime, 10)],
            logLevel=logLevel
        )

        self.isRegistered: threading.Event = threading.Event()
        self.appName: str = appName
        self.label: str = label
        self.showWindow: bool = showWindow
        self.videoPath: str = videoPath

        self.__lastDataSentTime = time()
        self.respondTime: Average = Average()

        if self.appName == 'FaceDetection':
            self.app: ApplicationUserSide = FaceDetection(
                appName=self.appName,
                videoPath=self.videoPath,
                targetWidth=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'FaceAndEyeDetection':
            self.app: ApplicationUserSide = FaceAndEyeDetection(
                appName=self.appName,
                videoPath=self.videoPath,
                targetWidth=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'ColorTracking':
            self.app: ApplicationUserSide = ColorTracking(
                appName=self.appName,
                videoPath=self.videoPath,
                targetWidth=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'VideoOCR':
            self.app: ApplicationUserSide = VideoOCR(
                appName=self.appName,
                videoPath=self.videoPath,
                targetWidth=int(self.label),
                showWindow=self.showWindow)
        else:
            self.logger.info('Application does not exist: %s', self.appName)
            os._exit(0)

    def run(self):
        self.__register()

    def __register(self):
        message = {
            'type': 'register',
            'role': 'user',
            'label': self.label,
            'appName': self.appName,
            'machineID': self.machineID}
        self.sendMessage(message, self.masterAddr)
        self.isRegistered.wait()
        self.logger.info("Registered. Waiting for resources to be ready ...")

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
        self.role = role
        self.setName(message)
        self.logger = get_logger(self.nameLogPrinting, self.logLevel)
        self.isRegistered.set()

    def __handleReady(self, message: Message):
        threading.Thread(target=self.__ready).start()

    def __ready(self):
        self.logger.info("Resources is ready.")
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
    appName_ = sys.argv[6]
    showWindow_ = sys.argv[7]
    label_ = sys.argv[8]
    videoPath_ = sys.argv[9] if len(sys.argv) > 9 else None
    user_ = User(
        myAddr=myAddr_,
        masterAddr=masterAddr_,
        loggerAddr=loggerAddr_,
        appName=appName_,
        label=label_,
        showWindow=True if showWindow_ == 'show' else False,
        videoPath=videoPath_)
    user_.run()
