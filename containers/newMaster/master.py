import threading
import logging

from logger import get_logger
from masterSideRegistry import Registry
from dataManagerServer import DataManagerServer
from message import Message
from queue import Empty
from datatype import Client, Worker, User, NodeSpecs, IO
from time import time, sleep
from exceptions import *
from systemInfo import SystemInfo


class MasterSysInfo(SystemInfo):
    def __init__(self, formatSize: bool):
        super().__init__(formatSize)
        self.res.receivedTasksCount = 0
        self.res.receivedDataSize = 0
        self.res.sentDataSize = 0
        self.res.changing += [
            'receivedTasksCount',
            'receivedDataSize',
            'sentDataSize'
        ]


class FogMaster:

    def __init__(self, host: str, port: int, id_: int = 0, logLevel=logging.DEBUG):

        self.logger = get_logger('Master', logLevel)
        self.masterID = id_
        self.host = host
        self.port = port
        self.__io = IO()

        self.dataManager = DataManagerServer(
            host=self.host,
            port=self.port,
            io=self.__io,
            logLevel=self.logger.level,
        )
        self.registry: Registry = Registry(logLevel=logLevel)
        self.__receivedTasksCount: int = 0

    def __nodeLogger(self):
        sysInfo = MasterSysInfo(formatSize=False)
        sleepTime = 10
        sysInfo.recordPerSeconds(seconds=sleepTime, logFilename='Master-%d-log.csv' % self.masterID)

        while True:
            sysInfo.res.receivedTasksCount = self.__receivedTasksCount
            sysInfo.res.receivedDataSize = self.__io.receivedSize
            sysInfo.res.sentDataSize = self.__io.sentSize
            sleep(sleepTime)

    def run(self):
        self.dataManager.run()
        threading.Thread(target=self.__serveUnregisteredClients).start()
        threading.Thread(target=self.__nodeLogger).start()

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
            for appID, worker in client.workerByAppID.items():
                self.registry.removeClient(worker)
            self.logger.debug(
                "UserID-%d disconnected",
                client.userID)
        elif isinstance(client, Worker):
            self.logger.debug(
                "WorkerID-%d disconnected",
                client.workerID)
        self.registry.removeClient(client)
        self.dataManager.discard(client)

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

    def __handleData(self, user: User, message: dict):
        self.__receivedTasksCount += 1
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
        userID = message['userID']
        user = self.registry.users[userID]
        message['type'] = 'result'
        self.dataManager.writeData(user, Message.encrypt(message))
        self.registry.workerWait(worker, appID=appID)


if __name__ == '__main__':
    master = FogMaster(host='0.0.0.0',
                       port=5000,
                       logLevel=logging.DEBUG)
    master.run()
