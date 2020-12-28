import logging
import threading
from logger import get_logger
from datatype import NodeSpecs
from dataManager import DataManager
from message import Message
from typing import NoReturn, Any


class Broker:

    def __init__(
            self,
            host: str,
            port: int,
            logLevel=logging.DEBUG):
        self.logger = get_logger('Worker-Broker', logLevel)
        self.host = host
        self.port = port
        self.workerID = None
        self.data: dict[int, dict[int, Any]] = {}
        self.dataManager: DataManager = DataManager(
            host=self.host,
            port=self.port,
            logLevel=self.logger.level)

    def run(self):
        self.dataManager.run()
        threading.Thread(target=self.receivedMessageHandler).start()
        self.register()

    def register(self) -> NoReturn:
        message = {'type': 'register',
                   'role': 'worker',
                   'nodeSpecs': NodeSpecs(1, 2, 3, 4),
                   'appIDs': [0, 1, 2, 3]}
        self.send(message)
        self.logger.info("[*] Registering ...")
        while self.workerID is None:
            pass
        self.logger.info("[*] Registered with workerID-%d", self.workerID)

    def send(self, data) -> NoReturn:
        self.dataManager.sendingQueue.put(Message.encrypt(data))

    def receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.dataManager.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'workerID':
                self.workerID = message['workerID']
            elif message['type'] == 'task':
                dataID = message['dataID']
                userID = message['userID']
                self.data[userID] = {}
                self.data[userID][dataID] = message['data']


if __name__ == '__main__':
    broker = Broker(
        host='127.0.0.1',
        port=5000,
        logLevel=logging.DEBUG)
    broker.run()
