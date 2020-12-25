import logging
import socketio
import threading
from logger import get_logger
from registryNamespace import RegistryNamespace
from taskNamespace import TaskNamespace
from dataManager import DataManager


class Broker:

    def __init__(
            self,
            serverHost: str,
            serverPort: int,
            dataHost: str,
            portReceiving: int,
            portSending: int,
            appList=None,
            logLevel=logging.DEBUG):
        self.logger = get_logger('Worker-Broker', logLevel)
        self.serverHost = serverHost
        self.serverPort = serverPort
        self.sio = socketio.Client()

        self.dataManager: DataManager = DataManager(
            host=dataHost,
            portSending=portSending,
            portReceiving=portReceiving,
            logLevel=self.logger.level)
        self.registryNamespace = RegistryNamespace(
            '/registry',
            logLevel=logLevel)
        self.taskNamespace = TaskNamespace(
            '/task',
            appList=appList,
            dataManager=self.dataManager,
            logLevel=logLevel)

    def run(self):
        threading.Thread(target=self.connect).start()
        while not self.registryNamespace.isRegistered:
            pass
        self.taskNamespace.updateWorkerID(self.registryNamespace.workerID)
        while not self.registryNamespace.isRegistered:
            pass
        self.logger.info("Got workerID-%d", self.taskNamespace.workerID)

    def connect(self):
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.sio.connect('%s:%d' % (self.serverHost, self.serverPort))
        self.sio.wait()


if __name__ == '__main__':
    from apps import appList

    broker = Broker(
        serverHost='http://127.0.0.1',
        serverPort=5000,
        dataHost='127.0.0.1',
        portSending=5001,
        portReceiving=5002,
        appList=appList,
        logLevel=logging.DEBUG)
    broker.run()
