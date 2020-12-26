import logging
import eventlet
import socketio

from logger import get_logger
from registry import Registry
from registryNamespace import RegistryNamespace
from taskManager import TaskManager
from taskNamespace import TaskNamespace
from dataManager import DataManager


class FogMaster:

    def __init__(self, host: str, portMain: int, portReceiving: int, portSending: int, logLevel=logging.DEBUG):
        self.logger = get_logger('Master', logLevel)

        self.host = host
        self.portMain = portMain
        self.portReceiving = portReceiving
        self.portSending = portSending

        self.taskManager: TaskManager = TaskManager(logLevel=logLevel)
        self.dataManager: DataManager = DataManager(host=self.host,
                                                    port=self.portReceiving,
                                                    portSending=self.portSending,
                                                    logLevel=logLevel)

        self.registry: Registry = Registry(logLevel=logLevel)

        self.sio: socketio.Server = socketio.Server()
        self.registryNamespace = RegistryNamespace(
            '/registry',
            registry=self.registry,
            logLevel=self.logger.level)
        self.taskNamespace = TaskNamespace(
            '/task',
            registry=self.registry,
            taskManager=self.taskManager,
            logLevel=self.logger.level)

    def run(self):
        self.dataManager.serve()
        app = socketio.WSGIApp(self.sio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'html/index.html'}
        })
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.logger.info("[*] Master serves at: %s:%d", self.host, self.portMain)
        eventlet.wsgi.server(eventlet.listen((self.host, self.portMain)),
                             app,
                             log=get_logger("EventLet", logging.DEBUG),
                             log_output=False)


if __name__ == '__main__':
    master = FogMaster(host='0.0.0.0',
                       portMain=5000,
                       portReceiving=5001,
                       portSending=5002,
                       logLevel=logging.DEBUG)
    master.run()
