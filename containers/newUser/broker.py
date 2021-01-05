import logging
import threading
import os

from time import time
from logger import get_logger
from dataManagerClient import DataManagerClient
from dataManagerServer import DataManagerServer
from message import Message
from typing import NoReturn
from queue import Queue
from typing import Any, List
from datatype import Master, Worker


class Broker:

    def __init__(
            self,
            masterIP: str,
            masterPort: int,
            thisIP: str,
            thisPort: int,
            appIDs: List[int],
            logLevel=logging.DEBUG):
        self.logger = get_logger('User-Broker', logLevel)
        self.masterIP = masterIP
        self.masterPort = masterPort
        self.thisIP = thisIP
        self.thisPort = thisPort
        self.userID = None
        self.appIDs = appIDs

        self.resultQueue: Queue = Queue()
        self.master: Master = Master(dataManager=DataManagerClient(
            name='Master',
            host=self.masterIP,
            port=self.masterPort,
            logLevel=self.logger.level
        ))

        self.workers: List[Worker] = []
        self.service: DataManagerServer = DataManagerServer(host=self.thisIP, port=thisPort)

    def run(self):
        self.service.run()
        self.master.dataManager.connect()
        threading.Thread(target=self.__receivedMessageHandler).start()
        self.register()

    def register(self) -> NoReturn:
        message = {'type': 'register', 'role': 'user', 'appIDs': self.appIDs}
        self.__send(message)
        self.logger.info("[*] Registering ...")
        while self.userID is None:
            pass
        self.logger.info("[*] Registered with userID-%d", self.userID)

    def __send(self, data) -> NoReturn:
        self.master.dataManager.sendingQueue.put(Message.encrypt(data))

    def __receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.master.dataManager.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'userID':
                self.userID = message['userID']
            elif message['type'] == 'result':
                self.resultQueue.put(message)
                message['time'].append(time() - message['time'][0])
                print(message['time'])
            elif message['type'] == 'refused':
                self.logger.warning(message['reason'])
                os._exit(0)

    def submit(self, data: Any, dataID: int, mode: str, appIDs: List[int]) -> NoReturn:
        message = {'time': [time()],
                   'type': 'submitData',
                   'mode': mode,
                   'appIDs': appIDs,
                   'data': data,
                   'dataID': dataID}
        # print('submit', time())
        self.__send(message)

    def registry(self):
        pass


if __name__ == '__main__':
    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        thisIP='127.0.0.1',
        thisPort=6000,
        appIDs=[]
    )
    broker.run()
