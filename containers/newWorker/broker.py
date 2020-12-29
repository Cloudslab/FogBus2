import logging
import threading
from logger import get_logger
from queue import Queue, Empty
from datatype import NodeSpecs
from dataManager import DataManager
from message import Message
from typing import NoReturn, Any, List
from datatype import ApplicationUserSide
from collections import defaultdict


class Broker:

    def __init__(
            self,
            host: str,
            port: int,
            apps: List[ApplicationUserSide],
            logLevel=logging.DEBUG):
        self.logger = get_logger('Worker-Broker', logLevel)
        self.host = host
        self.port = port
        self.apps: List[ApplicationUserSide] = apps
        self.workerID = None
        self.messageByAppID: dict[int, Queue] = defaultdict(Queue)
        self.dataManager: DataManager = DataManager(
            host=self.host,
            port=self.port,
            logLevel=self.logger.level)

    def run(self):
        self.dataManager.run()
        threading.Thread(target=self.__receivedMessageHandler).start()
        self.__register()
        for app in self.apps:
            self.__runApp(app)

    def __register(self) -> NoReturn:
        appIDs = []
        for app in self.apps:
            appIDs.append(app.appID)
        message = {'type': 'register',
                   'role': 'worker',
                   'nodeSpecs': NodeSpecs(1, 2, 3, 4),
                   'appIDs': appIDs}
        self.__send(message)
        self.logger.info("[*] Registering ...")
        while self.workerID is None:
            pass
        self.logger.info("[*] Registered with workerID-%d", self.workerID)

    def __send(self, message) -> NoReturn:
        self.dataManager.sendingQueue.put(Message.encrypt(message))

    def __receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.dataManager.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'workerID':
                self.workerID = message['workerID']
            elif message['type'] == 'data':
                appID = message['appID']
                self.messageByAppID[appID].put(message)

    def __runApp(self, app: ApplicationUserSide):
        self.logger.info('[*] AppID-%d-{%s} is serving ...', app.appID, app.appName)
        while True:
            try:
                message = self.messageByAppID[app.appID].get(block=False)
                threading.Thread(target=self.__executeApp, args=(app, message)).start()
            except Empty:
                continue

    def __executeApp(self, app: ApplicationUserSide, message) -> Any:
        self.logger.debug('Executing appID-%d ...', app.appID)
        data = message['data']
        result = app.process(data)
        message['result'] = result
        message['type'] = 'submitResult'
        message['workerID'] = self.workerID
        self.__send(message)
        self.logger.debug('Executed appID-%d and returned the result', app.appID)


if __name__ == '__main__':
    from apps import TestApp

    apps = [TestApp(appID=42, appName='Test Application')]
    broker = Broker(
        host='127.0.0.1',
        port=5000,
        apps=apps,
        logLevel=logging.DEBUG)
    broker.run()
