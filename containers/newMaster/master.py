import logging
import eventlet
import socketio

from logger import get_logger
from registry import Registry, RegistryNamespace
from taskManager import TaskManager
from taskNamespace import TaskNamespace
from taskCoordinator import TaskCoordinator
from dataManager import DataManager


class FogMaster:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.logger = get_logger('Master', logLevel)

        self.host = host
        self.port = port

        self.taskManager: TaskManager = TaskManager(logLevel=logLevel)
        self.dataManager: DataManager = DataManager(self.host, self.port, logLevel)

        self.registry: Registry = Registry(logLevel=logLevel)

        self.sio: socketio.Server = socketio.Server()
        self.registryNamespace = RegistryNamespace(
            '/registry',
            registry=self.registry,
            sio=self.sio,
            logLevel=self.logger.level)
        self.taskNamespace = TaskNamespace(
            '/task',
            registry=self.registry,
            sio=self.sio,
            taskManager=self.taskManager,
            logLevel=self.logger.level)

        self.taskCoordinator: TaskCoordinator = \
            TaskCoordinator(registry=self.registry,
                            taskNamespace=self.taskNamespace,
                            taskManager=self.taskManager,
                            dataManager=self.dataManager,
                            logLevel=self.logger.level)


    def run(self):
        self.taskCoordinator.run()

        app = socketio.WSGIApp(self.sio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'html/index.html'}
        })
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.logger.info("[*] Master serves at: %s:%d", self.host, self.port)
        eventlet.wsgi.server(eventlet.listen((self.host, self.port)),
                             app,
                             log=get_logger("EventLet", logging.DEBUG),
                             log_output=False)


if __name__ == '__main__':
    master = FogMaster('', 5000, logging.DEBUG)
    master.run()
