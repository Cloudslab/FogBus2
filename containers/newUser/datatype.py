import cv2
import socket
import logging
import threading
import os
import struct

from time import time, sleep
from logger import get_logger
from message import Message
from typing import NoReturn
from typing import List

from abc import abstractmethod
from typing import Any
from queue import Queue
from collections import defaultdict
from dataManagerClient import DataManagerClient
from systemInfo import SystemInfo


class NodeSpecs:
    def __init__(
            self,
            cores,
            ram,
            disk,
            network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network

    def info(self):
        return "\
                Cores: %d\n\
                ram: %d GB\n\
                disk: %d GB\n\
                network: %d Mbps\n" % (self.cores, self.ram, self.disk, self.cores)


class Master(DataManagerClient):
    def __init__(
            self,
            name: str = None,
            host: str = None,
            port: int = None,
            socket_: socket.socket = None,
            receivingQueue: Queue = None,
            sendingQueue: Queue = None,
            masterID: int = None,
            logLevel=logging.DEBUG):
        DataManagerClient.__init__(
            self,
            name=name,
            host=host,
            port=port,
            socket_=socket_,
            receivingQueue=receivingQueue,
            sendingQueue=sendingQueue,
            logLevel=logLevel
        )
        self.masterID = masterID


class UserSysInfo(SystemInfo):
    pass


class Broker:

    def __init__(
            self,
            masterIP: str,
            masterPort: int,
            taskIDs: List[int],
            remoteLoggerHost: str = None,
            remoteLoggerPort: int = None,
            logLevel=logging.DEBUG):
        self.logger = get_logger('User-Broker', logLevel)
        self.masterIP = masterIP
        self.masterPort = masterPort
        self.remoteLoggerHost: str = remoteLoggerHost
        self.remoteLoggerPort: int = remoteLoggerPort
        self.userID = None
        self.name = None
        self.taskIDs = taskIDs

        self.resultQueue: Queue = Queue()
        self.master: Master = Master(
            name='Master',
            host=self.masterIP,
            port=self.masterPort,
            logLevel=self.logger.level
        )

    def __nodeLogger(self):
        sysInfo = UserSysInfo(formatSize=False)
        sysInfo.recordPerSeconds(seconds=10, nodeName=self.name)
        threading.Thread(
            target=self.__sendLogToRemoteLogger,
            args=(sysInfo,)
        ).start()

    def __sendLog(self, message):
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.connect((self.remoteLoggerHost, self.remoteLoggerPort))

        messageEncrypted = Message.encrypt(message)
        serverSocket.sendall(struct.pack(">L", len(messageEncrypted)) + messageEncrypted)
        serverSocket.close()

    def __sendLogToRemoteLogger(self, sysInfo: UserSysInfo):
        if self.remoteLoggerHost is None \
                or self.remoteLoggerPort is None:
            return

        message = {
            'logList': sysInfo.res.keys(changing=False),
            'nodeName': self.name,
            'isChangingLog': False,
            'isTitle': True
        }
        self.__sendLog(message)
        message = {
            'logList': sysInfo.res.keys(changing=True),
            'nodeName': self.name,
            'isChangingLog': True,
            'isTitle': True
        }
        self.__sendLog(message)
        sleepTime = 10
        while True:
            sleep(sleepTime)
            message = {
                'logList': sysInfo.res.values(changing=True),
                'nodeName': self.name,
                'isChangingLog': True,
                'isTitle': False
            }
            self.__sendLog(message)

    def run(self, mode: str):
        self.master.link()
        threading.Thread(target=self.__receivedMessageHandler).start()
        self.register(mode=mode)

    def register(self, mode: str) -> NoReturn:
        message = {
            'type': 'register',
            'role': 'user',
            'mode': mode,
            'appIDs': self.taskIDs}
        self.__send(message)
        self.logger.info("[*] Registering ...")
        while self.userID is None:
            pass
        self.name = "User-%d" % self.userID
        threading.Thread(target=self.__nodeLogger).start()
        self.logger.info("[*] Registered with userID-%d", self.userID)

    def __send(self, data) -> NoReturn:
        self.master.sendingQueue.put(Message.encrypt(data))

    def __receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.master.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'userID':
                self.userID = message['userID']
            elif message['type'] == 'result':
                self.resultQueue.put(message)
                message['time'].append(time() - message['time'][0])
                print(message['time'])
            elif message['type'] == 'close':
                self.logger.warning(message['reason'])
                os._exit(0)

    def submit(
            self,
            data: Any,
            dataID: int,
            mode: str) -> NoReturn:
        message = {'time': [time()],
                   'type': 'submitData',
                   'mode': mode,
                   'appIDs': self.taskIDs,
                   'data': data,
                   'dataID': dataID}
        # print('submit', time())
        self.__send(message)


class ApplicationUserSide:

    def __init__(self, appID: int, broker: Broker, videoPath=None):
        self.appID = appID
        self.appName = None
        self.broker: Broker = broker
        self.capture = cv2.VideoCapture(0) if videoPath is None \
            else cv2.VideoCapture(videoPath)
        self.lockData: threading.Lock = threading.Lock()
        self.dataID = -1
        self.data: dict[int, Any] = {}
        self.result: dict[int, Queue] = defaultdict(Queue)
        self.dataIDSubmittedQueue = Queue()

    def createDataFrame(self, data: Any) -> (int, Any):
        self.lockData.acquire()
        self.dataID += 1
        dataID = self.dataID
        self.lockData.release()
        self.data[dataID] = data
        return dataID

    @abstractmethod
    def run(self):
        pass


if __name__ == '__main__':
    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        taskIDs=[]
    )
    broker.run()
