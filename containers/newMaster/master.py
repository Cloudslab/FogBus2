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
        elif messageDecrypted['type'] == 'submitData' \
                and client.socketID in self.registry.clientBySocketID:
            user = self.registry.clientBySocketID[client.socketID]
            if isinstance(user, User):
                self.__handleData(user, messageDecrypted)
        elif messageDecrypted['type'] == 'submitResult' \
                and client.socketID in self.registry.clientBySocketID:
            worker = self.registry.clientBySocketID[client.socketID]
            if isinstance(worker, Worker):
                self.__handleResult(worker, messageDecrypted)

    def __handleRegistration(self, client: Client, message: dict):
        client = self.registry.register(client, message)
        if isinstance(client, User):
            message = {'type': 'userID', 'userID': client.userID}
        elif isinstance(client, Worker):
            message = {'type': 'workerID', 'workerID': client.workerID}
        self.dataManager.writeData(client, Message.encrypt(message))

    def __handleData(self, user: User, message: dict):
        appID = message['appID']
        try:
            worker = self.registry.workerWork(appID)
            message['type'] = 'data'
            message['userID'] = user.userID
            self.dataManager.writeData(worker, Message.encrypt(message))
            self.logger.debug('Sent message from userID-%d with appID-%d to workerID-%d', user.userID, appID,
                              worker.workerID)
        except Empty:
            self.logger.debug('no worker for appID-%d', appID)

    def __handleResult(self, worker: Worker, message: dict):
        # TODO: use socket id to check the ownership of this task
        userID = message['userID']
        if userID in self.registry.users:
            user = self.registry.users[userID]
            message['type'] = 'result'
            self.dataManager.writeData(user, Message.encrypt(message))
        appID = message['appID']
        self.registry.workerWait(worker=worker, appID=appID)


if __name__ == '__main__':
    master = FogMaster(host='0.0.0.0',
                       port=5000,
                       logLevel=logging.DEBUG)
    master.run()
