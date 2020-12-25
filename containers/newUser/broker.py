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
            logLevel=logging.DEBUG):
        self.logger = get_logger('User-Broker', logLevel)
        self.serverHost = serverHost
        self.serverPort = serverPort
        self.dataHost = dataHost
        self.portReceiving = portReceiving
        self.portSending = portSending
        self.sio = socketio.Client()
        self.dataManager: DataManager = DataManager(
            host=self.dataHost,
            portSending=self.portSending,
            portReceiving=self.portReceiving,
            logLevel=self.logger.level)
        self.registryNamespace = RegistryNamespace(
            '/registry',
            logLevel=self.logger.level)
        self.taskNamespace = TaskNamespace(
            '/task',
            logLevel=self.logger.level)

    def run(self):
        threading.Thread(target=self.connect).start()
        while not self.registryNamespace.isRegistered:
            pass
        self.taskNamespace.setUserID(self.registryNamespace.userID)
        while not self.taskNamespace.isRegistered:
            pass
        self.logger.info("Got userID-%d", self.taskNamespace.userID)

    def connect(self):
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.sio.connect('%s:%d' % (self.serverHost, self.serverPort))
        self.sio.wait()

    def submit(self, appID, inputData):
        dataID = self.dataManager.sendData(inputData)
        self.taskNamespace.submit(appID=appID, dataID=dataID)
        resultID = self.taskNamespace.resultDataQueue.get()
        if resultID is None:
            return None
        resultData = self.dataManager.receiveData(resultID)
        return resultData


if __name__ == '__main__':
    broker = Broker(
        serverHost='http://127.0.0.1',
        serverPort=5000,
        dataHost='127.0.0.1',
        portSending=5001,
        portReceiving=5002,
        logLevel=logging.DEBUG)
    broker.run()
    print(broker.submit(1, 998))
