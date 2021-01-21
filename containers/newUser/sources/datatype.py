import cv2
import socket
import logging
import threading
import os
import struct

from time import time, sleep
from logger import get_logger
from message import encrypt, decrypt
from typing import NoReturn
from typing import List, Dict

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
            appName: str,
            masterAddr,
            logLevel=logging.DEBUG):

        self.masterAddr = masterAddr
        self.logger = get_logger('User-Broker', logLevel)
        self.userID = None
        self.name = None
        self.appName: str = appName
        self.label = None

        self.resultQueue: Queue = Queue()

    def run(self, label: str):
        self.label = label
        self.register()
        threading.Thread(target=self.__receivedMessageHandler).start()

    def register(self):
        message = {
            'type': 'register',
            'role': 'user',
            'appName': self.appName,
            'label': self.label
        }
        self.send(message)
        self.logger.info("[*] Registering ...")
        while self.userID is None:
            pass
        self.name = "%s@User-%d" % (self.label, self.userID)
        threading.Thread(target=self.__nodeLogger).start()
        self.logger.info("[*] Registered with userID-%d", self.userID)

    def send(self, data: Dict, retries: int = 3):
        if not retries:
            raise OSError
        try:
            clientSocket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM)
            clientSocket.connect(self.masterAddr)
            package = struct.pack(">L", len(data)) + data
            clientSocket.sendall(package)
            clientSocket.close()
        except OSError:
            self.send(data=data, retries=retries - 1)

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
            label: str,
            mode: str) -> NoReturn:
        message = {'time': [time()],
                   'type': 'submitData',
                   'mode': mode,
                   'data': data,
                   'dataID': dataID,
                   'label': label}
        # print('submit', time())
        self.__send(message)


class ApplicationUserSide:

    def __init__(self, appID: int, broker: Broker, videoPath=None, targetWidth: int = 640):
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
        self.targetWidth = targetWidth

    def createDataFrame(self, data: Any) -> (int, Any):
        self.lockData.acquire()
        self.dataID += 1
        dataID = self.dataID
        self.lockData.release()
        self.data[dataID] = data
        return dataID

    def resizeFrame(self, frame):
        width = frame.shape[1]
        height = frame.shape[0]
        resizedWidth = int(width * self.targetWidth / height)
        return cv2.resize(frame, (resizedWidth, self.targetWidth))

    @abstractmethod
    def run(self):
        pass


if __name__ == '__main__':
    pass
