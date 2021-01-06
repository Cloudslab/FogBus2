import logging
import threading

from logger import get_logger
from concurrent.futures import ThreadPoolExecutor
from masterSideRegistry import Registry
from taskManager import TaskManager
from dataManagerServer import DataManagerServer
from message import Message
from queue import Empty
from datatype import Client, Worker, User, NodeSpecs
from time import time
from exceptions import *
from queue import Queue


class FogMaster:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.logger = get_logger('Master', logLevel)
        self.host = host
        self.port = port
        self.dataManager = DataManagerServer(
            self.host,
            self.port,
            self.logger.level)
        self.taskManager: TaskManager = TaskManager(logLevel=logLevel)
        self.registry: Registry = Registry(logLevel=logLevel)

    def run(self):
        self.dataManager.run()
        threading.Thread(target=self.__serveUnregisteredClients).start()

    def __serveUnregisteredClients(self):
        self.logger.info('[*] Handling unregistered clients.')
        while True:
            client = self.dataManager.unregisteredClients.get()
            threading.Thread(
                target=self.__recogniseClient,
                args=(client,)).start()

    def __recogniseClient(self, client: Client):
        while True:
            try:
                message = client.receivingQueue.get(timeout=2)
                messageDecrypted = Message.decrypt(message)
                if messageDecrypted['type'] == 'register':
                    client = self.registry.register(
                        client,
                        messageDecrypted)
                    self.__serveClient(client)
                    break
            except (Empty, KeyError):
                self.dataManager.discard(client)
                break
            except NoWorkerAvailableException:
                break
            except WorkerCredentialNotValid:
                break

    def __serveClient(self, client: Client):
        message = None
        if isinstance(client, Worker):
            message = {'type': 'workerID', 'workerID': client.workerID}
        elif isinstance(client, User):
            message = {'type': 'userID', 'userID': client.userID}

        self.dataManager.writeData(client, Message.encrypt(message))
        while self.dataManager.hasClient(client):
            try:
                messageEncrypted = self.dataManager.readData(client)
                threading.Thread(
                    target=self.__handleMessage(
                        client,
                        messageEncrypted),
                    args=(client, messageEncrypted,)).start()
            except Empty:
                continue
            except (OSError, KeyError):
                break
        self.__discardClient(client)

    def __discardClient(self, client: Client):
        if isinstance(client, User):
            for _, appID in client.workerByAppID.keys():
                worker = client.workerByAppID[appID]
                self.registry.removeClient(worker, reason='Disconnected')
            self.dataManager.discard(client)
            self.logger.debug("UserID-%d disconnected", client.userID)
        if isinstance(client, Worker):
            for _, appID in client.userByAppID.keys():
                user = client.userByAppID[appID]
                self.registry.removeClient(user, reason='Disconnected')
            self.dataManager.discard(client)
            self.logger.debug("WorkerID-%d disconnected", client.workerID)

    def __handleMessage(self, client: Client, message: bytes):
        message = Message.decrypt(message)

        if isinstance(client, User):
            if message['type'] == 'submitData':
                self.__handleData(client, message)
            return
        if isinstance(client, Worker):
            if message['type'] == 'submitResult' \
                    and client.socketID in self.registry.clientBySocketID:
                worker = self.registry.clientBySocketID[client.socketID]
                if isinstance(worker, Worker):
                    self.__handleResult(worker, message)
                return
            if message['type'] == 'lookup':
                token = message['token']
                if token in self.registry.workerByToken:
                    worker = self.registry.workerByToken[token]
                    message = {'type': 'workerInfo',
                               'id': worker.workerID,
                               'ip': worker.ip,
                               'port': worker.port}
                    client.sendingQueue.put(Message.encrypt(message))
                    return

                self.__discardClient(client)

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
