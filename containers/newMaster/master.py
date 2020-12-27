import logging
import threading
import socket

from logger import get_logger
from registry import Registry
from taskManager import TaskManager
from dataManager import DataManager
from message import Message
from queue import Empty


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

    def __loopClients(self):
        while True:
            activeClients = self.dataManager.getActiveClients()
            for socketID in activeClients:
                try:
                    message = self.dataManager.readData(socketID)
                    threading.Thread(target=self.__messageHandler, args=(socketID, message)).start()
                except Empty:
                    continue

    def __messageHandler(self, socketID: int, message: bytes):
        messageDecrypted = Message.decrypt(message)
        if messageDecrypted['type'] == 'register':
            self.registry.register(socketID, messageDecrypted)
        elif messageDecrypted['type'] == 'submitTask':
            self.__handleTask(socketID, messageDecrypted)
        elif messageDecrypted['type'] == 'submitResult':
            self.__handleResult(socketID, messageDecrypted)

    def __handleTask(self, socketID: int, message: dict):
        pass

    def __handleResult(self, socketID: int, message: dict):
        pass


if __name__ == '__main__':
    master = FogMaster(host='0.0.0.0',
                       port=5000,
                       logLevel=logging.DEBUG)
    master.run()
