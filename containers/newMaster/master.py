import logging
import threading

from logger import get_logger
from registry import Registry
from taskManager import TaskManager
from dataManager import DataManager
from message import Message
from queue import Empty
from datatype import Client, Worker, User


class FogMaster:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.logger = get_logger('Master', logLevel)
        self.host = host
        self.port = port
        self.dataManager = DataManager(self.host, self.port, self.logger.level)
        self.taskManager: TaskManager = TaskManager(logLevel=logLevel)
        self.registry: Registry = Registry(logLevel=logLevel)

    def run(self):
        self.dataManager.run()
        threading.Thread(target=self.__loopClients).start()

    def __loopClients(self):
        self.logger.info('[*] Handling clients messages.')
        while True:
            activeClients = self.dataManager.getActiveClients()
            for client in activeClients:
                try:
                    message = self.dataManager.readData(client)
                    threading.Thread(target=self.__messageHandler, args=(client, message)).start()
                except Empty:
                    continue

    def __messageHandler(self, client: Client, message: bytes):
        messageDecrypted = Message.decrypt(message)
        if messageDecrypted['type'] == 'register':
            self.__handleRegistration(client, messageDecrypted)
        elif messageDecrypted['type'] == 'submitTask':
            self.__handleTask(client, messageDecrypted)
        elif messageDecrypted['type'] == 'submitResult':
            self.__handleResult(client, messageDecrypted)

    def __handleRegistration(self, client: Client, message: dict):
        client = self.registry.register(client, message)
        if isinstance(client, User):
            message = {'type': 'userID', 'userID': client.userID}
        elif isinstance(client, Worker):
            message = {'type': 'workerID', 'workerID': client.workerID}
        self.dataManager.writeData(client, Message.encrypt(message))

    def __handleTask(self, client: Client, message: dict):
        appID = message['appID']
        try:
            worker = self.registry.workerWork(appID)
            self.dataManager.writeData(worker, Message.encrypt(message))
        except Empty:
            self.logger.debug('no worker for appID-%d', appID)

    def __handleResult(self, client: Client, message: dict):
        # TODO: use socket id to check the ownership of this task
        userID = message['userID']
        if userID in self.registry.users:
            user = self.registry.users[userID]
            self.dataManager.writeData(user, Message.encrypt(message))
        workerID = message['workerID']
        appID = message['appID']
        worker = self.registry.workers[workerID]
        self.registry.workerWait(worker=worker, appID=appID)


if __name__ == '__main__':
    master = FogMaster(host='0.0.0.0',
                       port=5000,
                       logLevel=logging.DEBUG)
    master.run()
