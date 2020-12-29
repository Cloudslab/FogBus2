import logging
import threading

from logger import get_logger
from registry import Registry
from taskManager import TaskManager
from dataManager import DataManager
from message import Message
from queue import Empty
from datatype import Client, Worker, User
from time import time


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
        threading.Thread(target=self.__serveUnregisteredClients).start()

    def __serveUnregisteredClients(self):
        self.logger.info('[*] Handling unregistered clients.')
        while True:
            client = self.dataManager.unregisteredClients.get()
            threading.Thread(target=self.__recogniseClient, args=(client,)).start()

    def __recogniseClient(self, client: Client):
        message = self.dataManager.readData(client)
        messageDecrypted = Message.decrypt(message)
        if messageDecrypted['type'] == 'register':
            self.__handleRegistration(client, messageDecrypted)

    def __serveUser(self, user: User):
        message = {'type': 'userID', 'userID': user.userID}
        self.dataManager.writeData(user, Message.encrypt(message))
        while True:
            messageEncrypted = self.dataManager.readData(user)
            threading.Thread(target=self.__handleUserMessage, args=(user, messageEncrypted,)).start()

    def __handleUserMessage(self, user: User, message: bytes):
        messageDecrypted = Message.decrypt(message)
        if messageDecrypted['type'] == 'submitData':
            self.__handleData(user, messageDecrypted)

    def __serveWorker(self, worker: Worker):
        message = {'type': 'workerID', 'workerID': worker.workerID}
        self.dataManager.writeData(worker, Message.encrypt(message))
        while True:
            messageEncrypted = self.dataManager.readData(worker)
            threading.Thread(target=self.__handleWorkerMessage, args=(worker, messageEncrypted,)).start()

    def __handleWorkerMessage(self, worker: Worker, message: bytes):
        messageDecrypted = Message.decrypt(message)
        if messageDecrypted['type'] == 'submitResult' \
                and worker.socketID in self.registry.clientBySocketID:
            worker = self.registry.clientBySocketID[worker.socketID]
            if isinstance(worker, Worker):
                self.__handleResult(worker, messageDecrypted)

    def __handleRegistration(self, client: Client, message: dict):
        client = self.registry.register(client, message)
        if isinstance(client, User):
            self.__serveUser(client)
        elif isinstance(client, Worker):
            self.__serveWorker(client)

    def __handleData(self, user: User, message: dict):
        appID = message['appID']
        worker = self.registry.workerWork(appID)
        message['type'] = 'data'
        message['userID'] = user.userID
        message['time'].append(time() - message['time'][0])
        print('sending handling', time())
        self.dataManager.writeData(worker, Message.encrypt(message))
        self.logger.debug('Sent message from userID-%d with appID-%d to workerID-%d', user.userID, appID,
                          worker.workerID)

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
