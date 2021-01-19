import threading
import logging
import socket
import struct
import os
import sys

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

    def __init__(
            self,
            host: str,
            port: int,
            id_: int = 0,
            remoteLoggerHost: str = None,
            remoteLoggerPort: int = None,
            logLevel=logging.DEBUG):

        self.logger = get_logger('Master', logLevel)
        self.masterID = id_
        self.name = 'Master-%d' % self.masterID
        self.host = host
        self.port = port
        self.remoteLoggerHost: str = remoteLoggerHost
        self.remoteLoggerPort: int = remoteLoggerPort
        self.__io = IO()

        self.dataManager = DataManagerServer(
            host=self.host,
            port=self.port,
            io=self.__io,
            logLevel=self.logger.level,
        )

        self.registry: Registry = Registry(
            logLevel=logLevel
        )
        self.__receivedTasksCount: int = 0

    def __nodeLogger(self):
        sysInfo = MasterSysInfo(formatSize=False)
        sleepTime = 10
        sysInfo.recordPerSeconds(seconds=sleepTime, nodeName=self.name)
        threading.Thread(
            target=self.__sendLogToRemoteLogger,
            args=(sysInfo,)
        ).start()
        while True:
            sysInfo.res.receivedTasksCount = self.__receivedTasksCount
            sysInfo.res.receivedDataSize = self.__io.receivedSize
            sysInfo.res.sentDataSize = self.__io.sentSize
            sleep(sleepTime)

    def __sendLog(self, message):
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.connect((self.remoteLoggerHost, self.remoteLoggerPort))

        messageEncrypted = Message.encrypt(message)
        serverSocket.sendall(struct.pack(">L", len(messageEncrypted)) + messageEncrypted)
        serverSocket.close()

    def __sendLogToRemoteLogger(self, sysInfo: MasterSysInfo):
        if self.remoteLoggerHost is None \
                or self.remoteLoggerPort is None:
            return

        message = {
            'logList': sysInfo.res.keys(changing=False),
            'nodeName': "Master-%d" % self.masterID,
            'isChangingLog': False,
            'isTitle': True
        }
        self.__sendLog(message)
        message = {
            'logList': sysInfo.res.keys(changing=True),
            'nodeName': "Master-%d" % self.masterID,
            'isChangingLog': True,
            'isTitle': True
        }
        self.__sendLog(message)
        sleepTime = 10
        while True:
            sleep(sleepTime)
            message = {
                'logList': sysInfo.res.values(changing=True),
                'nodeName': "Master-%d" % self.masterID,
                'isChangingLog': True,
                'isTitle': False
            }
            self.__sendLog(message)

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
                import traceback
                traceback.print_exc()
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
                self.recordDataTransferring(client)
                threading.Thread(
                    target=self.__handleMessage(
                        client,
                        messageEncrypted),
                    args=(client, messageEncrypted,)).start()
            except Empty:
                continue
            except OSError:
                import traceback
                traceback.print_exc()
                break
            except KeyError:
                continue
        self.__discardClient(client)

    def __discardClient(self, client: Client):
        if isinstance(client, User):
            for appID, worker in client.taskByName.items():
                self.registry.removeClient(worker)
        self.registry.removeClient(client)
        self.dataManager.discard(client)
        self.logger.debug(
            "%s disconnected.",
            client.name
        )

    def recordDataTransferring(self, client):
        if client.name is None:
            return
        filename = 'AverageIO@%s@%s.csv ' % (self.name, client.name)
        fileContent = 'averageReceivedPackageSize, ' \
                      'averageSentPackageSize, ' \
                      'lowestReceivingSpeed, ' \
                      'highestReceivingSpeed, ' \
                      'lowestSendingSpeed, ' \
                      'highestSendingSpeed\r\n' \
                      '%f, %f, %f, %f, %f, %f\r\n' % (
                          client.connectionIO.averageReceivedPackageSize,
                          client.connectionIO.averageSentPackageSize,
                          client.connectionIO.lowestReceivingSpeed,
                          client.connectionIO.highestReceivingSpeed,
                          client.connectionIO.lowestSendingSpeed,
                          client.connectionIO.highestSendingSpeed
                      )
        self.writeFile(filename, fileContent)

    @staticmethod
    def writeFile(name, content):
        logPath = './log'
        if not os.path.exists(logPath):
            os.mkdir(logPath)
        f = open('%s/%s' % (logPath, name), 'w')
        f.write(content)
        f.close()

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
                    self.__handleResult(message)
                return
            if message['type'] == 'lookup':
                token = message['token']
                print(message, self.registry.workerByToken)

                if token in self.registry.workerByToken:
                    worker = self.registry.workerByToken[token]
                    message = {'type': 'workerInfo',
                               'id': worker.workerID,
                               'ip': worker.ip,
                               'port': worker.port,
                               'name': worker.name
                               }
                    print(message)
                    client.sendingQueue.put(Message.encrypt(message))
                    return

    def __handleData(self, user: User, message: dict):
        self.__receivedTasksCount += 1
        message['type'] = 'data'
        message['userID'] = user.userID
        message['time'].append(time() - message['time'][0])

        for taskName in user.entranceTasksByName:
            worker = user.taskByName[taskName]
            self.dataManager.writeData(worker, Message.encrypt(message))
            self.recordDataTransferring(worker)
            self.logger.debug(
                'Got data from %s and assigned to %s',
                user.name,
                worker.name)

    def __handleResult(self, message: dict):
        # TODO: use socket id to check the ownership of this task
        userID = message['userID']
        user = self.registry.users[userID]
        message['type'] = 'result'
        self.dataManager.writeData(user, Message.encrypt(message))


if __name__ == '__main__':
    remoteLoggerHost = sys.argv[1]
    remoteLoggerPort = int(sys.argv[2])
    master = FogMaster(host='0.0.0.0',
                       port=5000,
                       remoteLoggerHost=remoteLoggerHost,
                       remoteLoggerPort=remoteLoggerPort,
                       logLevel=logging.DEBUG)
    master.run()
