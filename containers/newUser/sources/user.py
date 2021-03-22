import os
import json
import argparse
from apps import *
from node import Node
from connection import Message, Identity, Connection
from exceptions import *
from logger import get_logger
from time import time, sleep
from typing import List, Tuple

Address = Tuple[str, int]


class ResponseTime:

    def __init__(self):
        self.__maxRecordNumber = 100
        self.__sentTimeTable: List[float] = [0 for _ in range(self.__maxRecordNumber)]


class User(Node):

    def __init__(
            self,
            containerName,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            appName: str,
            showWindow: bool,
            label: str,
            videoPath: str,
            logLevel=logging.DEBUG):
        self.containerName = containerName
        Node.__init__(
            self,
            role='User',
            containerName=containerName,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[
                (self.__uploadMedianRespondTime, 10)],
            logLevel=logLevel
        )

        self.isRegistered: threading.Event = threading.Event()
        self.appName: str = appName
        self.label: str = label
        self.showWindow: bool = showWindow
        self.videoPath: str = videoPath

        self.__lastDataSentTime = time()
        self.workersCount = 0

        if self.appName == 'FaceDetection':
            self.app: ApplicationUserSide = FaceDetection(
                appName=self.appName,
                videoPath=self.videoPath,
                targetHeight=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'FaceAndEyeDetection':
            self.app: ApplicationUserSide = FaceAndEyeDetection(
                appName=self.appName,
                videoPath=self.videoPath,
                targetHeight=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'ColorTracking':
            self.app: ApplicationUserSide = ColorTracking(
                appName=self.appName,
                videoPath=self.videoPath,
                targetHeight=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'VideoOCR':
            self.app: ApplicationUserSide = VideoOCR(
                appName=self.appName,
                videoPath=self.videoPath,
                targetHeight=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'GameOfLifeSerialised':
            self.app: ApplicationUserSide = GameOfLifeSerialised(
                appName=self.appName,
                videoPath=self.videoPath,
                targetHeight=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'GameOfLifeParallelized':
            self.app: ApplicationUserSide = GameOfLifeParallelized(
                appName=self.appName,
                videoPath=self.videoPath,
                targetHeight=int(self.label),
                showWindow=self.showWindow)
        elif self.appName == 'GameOfLifePyramid':
            self.app: ApplicationUserSide = GameOfLifePyramid(
                appName=self.appName,
                videoPath=self.videoPath,
                targetHeight=int(self.label),
                showWindow=self.showWindow)
        else:
            self.logger.info('Application does not exist: %s', self.appName)
            os._exit(0)

    def run(self):
        self.__register()

    def __waitForWorkers(self):
        targetCount = 5
        msg = {'type': 'workersCount'}
        count = 3000
        while count > 0:
            self.sendMessage(msg, self.master.addr)
            sleep(1)
            count -= 1
            if self.workersCount >= targetCount:
                break
            self.logger.info(
                'Waiting for enough workers '
                '[%d/%d]' % (self.workersCount, targetCount))
        sleep(1)

    def __register(self):
        self.logger = get_logger('User', logging.DEBUG)
        self.__registerAt(self.masterAddr)
        self.isRegistered.wait()

    def handleMessage(self, message: Message):
        if message.type == 'registered':
            self.__handleRegistered(message)
        elif message.type == 'ready':
            self.__handleReady()
        elif message.type == 'result':
            self.__handleResult(message)
        elif message.type == 'workersCount':
            self.__handleWorkersCount(message)
        elif message.type == 'forward':
            self.__handleForward(message)

    def __handleRegistered(self, message: Message):
        self.logger.info("Registered at %s"
                         ". Waiting for resources to be ready ..." % str(message.source.addr))
        role = message.content['role']
        if not role == 'User':
            raise RegisteredAsWrongRole
        self.id = message.content['id']
        self.role = role
        self.setName(message)
        self.logger = get_logger(self.nameLogPrinting, self.logLevel)
        self.isRegistered.set()

    def __handleReady(self):
        threading.Thread(target=self.__ready).start()

    def __handleResult(self, message: Message):
        result = message.content['result']
        self.app.result.put(result)
        self.__saveRespondTime()

    def __handleWorkersCount(self, message: Message):
        self.workersCount = message.content['workersCount']

    def __handleForward(self, message: Message):
        newMasterIP = message.content['ip']
        # give the new Master some time to rise
        self.logger.info(
            'Request is forwarding to %s' % str(newMasterIP))
        newMasterAddr = (newMasterIP, 5000)
        self.logger.info(
            'Lookup Master at %s' % str(newMasterAddr)
        )
        while not self.__testConnectivity(newMasterAddr):
            sleep(1)

        self.logger.info(
            'Found Master at %s' % str(newMasterAddr)
        )
        self.__registerAt(newMasterAddr)

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
            self.sendMessage(message, self.master.addr)
            self.__lastDataSentTime = time()

    def __uploadMedianRespondTime(self):
        if self.app.respondTime.median() is None:
            return
        msg = {
            'type': 'respondTime',
            'respondTime': self.app.respondTime.median()}
        self.sendMessage(msg, self.remoteLogger.addr)

    def __saveRespondTime(self):
        if self.app.respondTimeCount > 5:
            return
        logFilename = 'log/respondTime.json'
        if os.path.exists(logFilename):
            return
        self.logger.info(self.app.respondTimeCount)
        if not os.path.exists('log'):
            os.mkdir('log')
        with open(logFilename, 'w+') as f:
            content = {self.nameLogPrinting: self.app.respondTime.median()}
            json.dump(content, f)
            f.close()
            self.logger.info(content)

    @staticmethod
    def __testConnectivity(addr: Address):
        try:
            Connection(addr).send({})
            return True
        except Exception:
            return False

    def __registerAt(self, masterAddr: Address):
        self.masterAddr = masterAddr
        self.master = Identity(
            nameLogPrinting='Master',
            addr=self.masterAddr,
        )
        self.__waitForWorkers()
        message = {
            'type': 'register',
            'role': 'User',
            'label': self.label,
            'appName': self.appName,
            'machineID': self.machineID}
        self.sendMessage(message, self.master.addr)
        self.logger.info('Sent registration to  %s ...' % str(self.master.addr))


def parseArg():
    parser = argparse.ArgumentParser(
        description='User'
    )
    parser.add_argument(
        'containerName',
        metavar='ContainerName',
        type=str,
        help='Current container name, used for getting runtime usages.'
    )
    parser.add_argument(
        'ip',
        metavar='BindIP',
        type=str,
        help='User ip.'
    )
    parser.add_argument(
        'masterIP',
        metavar='MasterIP',
        type=str,
        help='Master ip.'
    )
    parser.add_argument(
        'masterPort',
        metavar='MasterPort',
        type=int,
        help='Master port'
    )
    parser.add_argument(
        'loggerIP',
        metavar='RemoteLoggerIP',
        type=str,
        help='Remote logger ip.'
    )
    parser.add_argument(
        'loggerPort',
        metavar='RemoteLoggerPort',
        type=int,
        help='Remote logger port'
    )
    parser.add_argument(
        'appName',
        metavar='AppName',
        type=str,
        help='Application Name'
    )
    parser.add_argument(
        'label',
        metavar='Label',
        type=int,
        help='e.g. 480 or 720'
    )
    parser.add_argument(
        '--video',
        metavar='VideoPath',
        nargs='?',
        default=0,
        type=str,
        help='/path/to/video.mp4'
    )
    parser.add_argument(
        '--showWindow',
        metavar='ShowWindow',
        default=True,
        action=argparse.BooleanOptionalAction,
        help='Show window or not'
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parseArg()
    user_ = User(
        containerName=args.containerName,
        myAddr=(args.ip, 0),
        masterAddr=(args.masterIP, args.masterPort),
        loggerAddr=(args.loggerIP, args.loggerPort),
        appName=args.appName,
        label=args.label,
        showWindow=args.showWindow,
        videoPath=args.video)
    user_.run()
