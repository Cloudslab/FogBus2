import logging
import threading

from time import time
from logger import get_logger
from dataManager import DataManager
from message import Message
from typing import NoReturn
from queue import Queue
from typing import Any, List


class Broker:

    def __init__(
            self,
            host: str,
            port: int,
            appIDs: List[int],
            logLevel=logging.DEBUG):
        self.logger = get_logger('User-Broker', logLevel)
        self.host = host
        self.port = port
        self.userID = None
        self.appIDs = appIDs

        self.resultQueue: Queue = Queue()
        self.dataManager: DataManager = DataManager(
            host=self.host,
            port=self.port,
            logLevel=self.logger.level)

    def run(self):
        self.dataManager.run()
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
        self.dataManager.sendingQueue.put(Message.encrypt(data))

    def __receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.dataManager.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'userID':
                self.userID = message['userID']
            elif message['type'] == 'result':
                self.resultQueue.put(message)
                message['time'].append(time() - message['time'][0])
                print(message['time'])

    def submit(self, appID: int, data: Any, dataID: int) -> NoReturn:
        message = {'time': [time()],
                   'type': 'submitData',
                   'appID': appID,
                   'data': data,
                   'dataID': dataID}
        # print('submit', time())
        self.__send(message)
