import logging
import threading
from logger import get_logger
from dataManager import DataManager
from message import Message
from typing import NoReturn, Any


class Broker:

    def __init__(
            self,
            host: str,
            port: int,
            logLevel=logging.DEBUG):
        self.logger = get_logger('User-Broker', logLevel)
        self.host = host
        self.port = port
        self.userID = None
        self.data: dict[int, Any] = {}
        self.dataManager: DataManager = DataManager(
            host=self.host,
            port=self.port,
            logLevel=self.logger.level)

    def run(self):
        self.dataManager.run()
        threading.Thread(target=self.receivedMessageHandler).start()
        self.register()

    def register(self) -> NoReturn:
        message = {'type': 'register', 'role': 'user'}
        self.send(message)
        self.logger.info("[*] Registering ...")
        while self.userID is None:
            pass
        self.logger.info("[*] Registered with userID-%d", self.userID)

    def send(self, data) -> NoReturn:
        self.dataManager.sendingQueue.put(Message.encrypt(data))

    def receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.dataManager.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'userID':
                self.userID = message['userID']
            elif message['type'] == 'result':
                dataID = message['dataID']
                self.data[dataID] = message['data']


if __name__ == '__main__':
    broker = Broker(
        host='127.0.0.1',
        port=5000,
        logLevel=logging.DEBUG)
    broker.run()
