import logging
import threading

from logger import get_logger
from masterSideRegistry import Registry
from taskManager import TaskManager
from dataManagerServer import DataManagerServer
from message import Message
from queue import Empty
from datatype import Client, Worker, User
from time import time
from exceptions import *


class FogMaster:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.logger = get_logger('Master', logLevel)
        self.host = host
        self.port = port
        self.dataManager = DataManagerServer(self.host, self.port, self.logger.level)
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
        try:
            message = self.dataManager.readData(client)
            messageDecrypted = Message.decrypt(message)
            if messageDecrypted['type'] == 'register':
                self.__handleRegistration(client, messageDecrypted)
        except Empty:
            self.dataManager.discard(client)

    def __serveUser(self, user: User):
        message = {'type': 'userID', 'userID': user.userID}
        self.dataManager.writeData(user, Message.encrypt(message))
        while True:
            try:
                messageEncrypted = self.dataManager.readData(user)
                threading.Thread(target=self.__handleUserMessage, args=(user, messageEncrypted,)).start()
            except Empty:
                if user.active:
                    continue
                self.__discardUser(user)

    def __discardUser(self, user: User):
        for _, appID in user.workerByAppID.keys():
            worker = user.workerByAppID[appID]
            del worker.userByAppID[appID]
            self.registry.workerWait(worker, appID)
        self.dataManager.discard(user)
        self.logger.debug("UserID-%d disconnected", user.userID)

    def __handleUserMessage(self, user: User, message: bytes):
        messageDecrypted = Message.decrypt(message)
        if messageDecrypted['type'] == 'submitData':
            self.__handleData(user, messageDecrypted)

    def __discardWorker(self, worker: Worker):
        for _, appID in worker.userByAppID.keys():
            user = worker.userByAppID[appID]
            del user.workerByAppID[appID]
        self.dataManager.discard(worker)
        self.logger.debug("WorkerID-%d disconnected", worker.workerID)

    def __serveWorker(self, worker: Worker):
        message = {'type': 'workerID', 'workerID': worker.workerID}
        self.dataManager.writeData(worker, Message.encrypt(message))
        while True:
            try:
                messageEncrypted = self.dataManager.readData(worker)
                threading.Thread(target=self.__handleWorkerMessage, args=(worker, messageEncrypted,)).start()
            except Empty:
                if worker.active:
                    continue
                self.__discardWorker(worker)

    def __handleWorkerMessage(self, worker: Worker, message: bytes):
        messageDecrypted = Message.decrypt(message)
        if messageDecrypted['type'] == 'submitResult' \
                and worker.socketID in self.registry.clientBySocketID:
            worker = self.registry.clientBySocketID[worker.socketID]
            if isinstance(worker, Worker):
                self.__handleResult(worker, messageDecrypted)

    def __handleRegistration(self, client: Client, message: dict):
        try:
            client = self.registry.register(client, message)
            if isinstance(client, User):
                self.__serveUser(client)
            elif isinstance(client, Worker):
                self.__serveWorker(client)
        except NoWorkerAvailableException as e:
            message = {'type': 'refused', 'reason': str(e)}
            self.dataManager.writeData(client, Message.encrypt(message))

    def __handleData(self, user: User, message: dict):

        message['type'] = 'data'
        message['userID'] = user.userID
        message['time'].append(time() - message['time'][0])

        mode = message['mode']
        appIDs = message['appIDs']
        if mode == 'sequential':
            nextAppID = appIDs[0]
            worker = user.workerByAppID[nextAppID]
            self.dataManager.writeData(worker, Message.encrypt(message))
            self.logger.debug('Sent message from userID-%d with appID-%d to workerID-%d', user.userID, nextAppID,
                              worker.workerID)
        elif mode == 'parallel':
            for appID in appIDs:
                message['appIDs'] = [appID]
                worker = user.workerByAppID[appID]
                self.dataManager.writeData(worker, Message.encrypt(message))
                self.logger.debug('Sent message from userID-%d with appID-%d to workerID-%d', user.userID, appID,
                                  worker.workerID)

    def __handleResult(self, worker: Worker, message: dict):
        # TODO: use socket id to check the ownership of this task
        appID = message['appID']
        user = worker.userByAppID[appID]
        if len(message['appIDs']):
            message['type'] = 'data'
            nextWorker = user.workerByAppID[message['appIDs'][0]]
            self.dataManager.writeData(nextWorker, Message.encrypt(message))
        else:
            message['type'] = 'result'
            self.dataManager.writeData(user, Message.encrypt(message))
            self.registry.workerWait(worker, appID=appID)


if __name__ == '__main__':
    master = FogMaster(host='0.0.0.0',
                       port=5000,
                       logLevel=logging.DEBUG)
    master.run()
