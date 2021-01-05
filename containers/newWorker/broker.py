import logging
import threading
from logger import get_logger
from queue import Queue, Empty
from datatype import NodeSpecs
from dataManagerClient import DataManagerClient
from dataManagerServer import DataManagerServer
from message import Message
from typing import NoReturn, Any, List
from datatype import ApplicationUserSide, Master, Worker, Node
from collections import defaultdict
from time import time


class Broker:

    def __init__(
            self,
            masterIP: str,
            masterPort: int,
            thisIP: str,
            thisPort: int,
            appIDs: List[ApplicationUserSide],
            logLevel=logging.DEBUG):
        self.logger = get_logger('Worker-Broker', logLevel)
        self.masterIP = masterIP
        self.masterPort = masterPort
        self.thisIP = thisIP
        self.thisPort = thisPort
        self.appIDs: List[ApplicationUserSide] = appIDs
        self.workerID = None
        self.messageByAppID: dict[int, Queue] = defaultdict(Queue)
        self.master: Master = Master(
            name='Master',
            host=self.masterIP,
            port=self.masterPort,
            logLevel=self.logger.level
        )

        self.workers: List[Worker] = []
        self.service: DataManagerServer = DataManagerServer(
            host=self.thisIP,
            port=thisPort)

    def run(self):
        self.service.run()
        self.master.link()
        threading.Thread(target=self.__receivedMessageHandler).start()
        self.__register()
        for app in self.appIDs:
            threading.Thread(target=self.__runApp, args=(app,)).start()

    def __handleClients(self):

        while True:
            worker = self.service.unregisteredClients.get()
            registrationInfo = worker.receivingQueue.get()
            registrationInfo = Message.decrypt(registrationInfo)
            workerID = registrationInfo['workerID']
            worker.workerID = workerID
            self.workers[workerID] = worker

    def __register(self) -> NoReturn:
        appIDs = []
        for app in self.appIDs:
            appIDs.append(app.appID)
        message = {'type': 'register',
                   'role': 'worker',
                   'addr': (self.thisIP, self.thisPort),
                   'nodeSpecs': NodeSpecs(1, 2, 3, 4),
                   'appIDs': appIDs}
        self.__sendTo(self.master, message)
        self.logger.info("[*] Registering ...")
        while self.workerID is None:
            pass
        self.logger.info("[*] Registered with workerID-%d", self.workerID)

    @staticmethod
    def __sendTo(target: DataManagerClient, message: Any) -> NoReturn:
        target.sendingQueue.put(Message.encrypt(message))

    def __receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.master.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'workerID':
                self.workerID = message['workerID']
            elif message['type'] == 'data':
                appID = message['appIDs'][0]
                self.messageByAppID[appID].put(message)

    def __runApp(self, app: ApplicationUserSide):
        self.logger.info('[*] AppID-%d-{%s} is serving ...', app.appID, app.appName)
        while True:
            message = self.messageByAppID[app.appID].get()
            self.__executeApp(app, message)

    def __executeApp(self, app: ApplicationUserSide, message) -> NoReturn:
        self.logger.debug('Executing appID-%d ...', app.appID)
        data = message['data']
        result = app.process(data)
        message['type'] = 'submitResult'
        message['workerID'] = self.workerID
        message['appID'] = app.appID
        message['appIDs'] = message['appIDs'][1:]

        t = time() - message['time'][0]
        message['time'].append(t)

        if len(message['appIDs']):
            message['data'] = result
        else:
            del message['data']
            message['result'] = result
        self.__sendTo(self.master, message)
        self.logger.debug('Executed appID-%d and returned the result', app.appID)


if __name__ == '__main__':
    from apps import TestApp

    apps = [TestApp(appID=42)]
    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        thisIP='127.0.0.1',
        thisPort=6000,
        appIDs=apps,
        logLevel=logging.DEBUG)
    broker.run()
