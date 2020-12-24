import logging
import socketio
import threading
from logger import get_logger
from registryNamespace import RegistryNamespace
from taskNamespace import TaskNamespace


class Broker:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.logger = get_logger('WorkerSideBroker', logLevel)
        self.host = host
        self.port = port
        self.sio = socketio.Client()
        self.registryNamespace = RegistryNamespace('/registry', logLevel=logLevel)
        self.taskNamespace = TaskNamespace('/task', logLevel=logLevel)

    def run(self):
        threading.Thread(target=self.connect).start()
        while not self.taskNamespace.isConnected or \
                not self.registryNamespace.connected:
            pass
        self.registryNamespace.register()
        while self.registryNamespace.workerID is None:
            pass
        self.taskNamespace.workerID = self.registryNamespace.workerID
        self.taskNamespace.register()
        while not self.taskNamespace.isRegistered:
            pass
        self.logger.info("Got workerID-%d", self.taskNamespace.workerID)

    def connect(self):
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.sio.connect('%s:%d' % (self.host, self.port))
        self.sio.wait()


if __name__ == '__main__':
    broker = Broker('http://127.0.0.1', 5000, logLevel=logging.DEBUG)
    broker.run()
