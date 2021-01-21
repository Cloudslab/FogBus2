import logging
import sys
import threading
from datatype import Broker
from apps import *
from node import Node
from connection import Message
from exceptions import *
from logger import get_logger
from typing import Dict


class User(Node):

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
            appName,
            label,
            logLevel=logging.DEBUG):
        super().__init__(
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            logLevel=logLevel
        )

        self.isRegistered: threading.Event = threading.Event()
        self.userID: int = None
        self.appName = appName
        self.label = label
        self.app: ApplicationUserSide = None

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
        self.userID = message.content['id']
        self.name = message.content['name']
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
            os._exit(0)
        self.app.run()
        self.logger.info('Running ...')

        while True:
            data = self.app.dataToSubmit.get()
            message = {
                'type': 'data',
                'userID': self.userID,
                'data': data}
            self.sendMessage(message, self.masterAddr)

    def __handleResult(self, message: Message):
        result = message.content['result']
        self.app.result.put(result)


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

    # remoteLoggerHost = sys.argv[1]
    # masterPort = int(sys.argv[2])
    # appIDOrName = sys.argv[3]
    # targetWidth = int(sys.argv[4])
    # videoPath = sys.argv[5] if len(sys.argv) > 5 else None
    # broker = Broker(
    #     masterIP=remoteLoggerHost,
    #     masterPort=masterPort,
    #     remoteLoggerHost='127.0.0.1',
    #     remoteLoggerPort=5001,
    #     appName=appIDOrName,
    #     logLevel=logging.DEBUG)
    # app = None
    # if appIDOrName == 'FaceDetection':
    #     app = FaceDetection(1, broker, videoPath, targetWidth=targetWidth)
    # elif appIDOrName == 'FaceAndEyeDetection':
    #     app = FaceAndEyeDetection(2, broker, videoPath, targetWidth=targetWidth)
    # elif appIDOrName == 'ColorTracking':
    #     app = ColorTracking(3, broker, videoPath, targetWidth=targetWidth)
    # elif appIDOrName == 'VideoOCR':
    #     app = VideoOCR(4, broker, videoPath, targetWidth=targetWidth)
    # if app is not None:
    #     app.run()
