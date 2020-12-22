import logging
import threading
from queue import Queue
import eventlet
import socketio
import cv2

from logger import get_logger
from registry import Registry, RegistryNamespace
from task import TaskManager, TaskNamespace
from datatype import Master, NodeSpecs
from message import Message


class FogMaster:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.host = host
        self.port = port
        self.sio = socketio.Server()
        self.registry = Registry()
        self.taskManager = TaskManager(registry=self.registry)
        self.logger = get_logger('Master', logLevel)

    def run(self):
        app = socketio.WSGIApp(self.sio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'html/index.html'}
        })
        self.sio.register_namespace(RegistryNamespace(
            '/registry', registry=self.registry, sio=self.sio, logLevel=self.logger.level))

        self.sio.register_namespace(TaskNamespace(
            '/task', taskManager=self.taskManager, sio=self.sio, logLevel=self.logger.level))

        self.logger.info("[*] Master serves at: %s:%d", self.host,  self.port)

        eventlet.wsgi.server(eventlet.listen((self.host,  self.port)),
                             app,
                             log=get_logger("EventLet", logging.DEBUG),
                             log_output=False)


if __name__ == '__main__':

    master = FogMaster('', 5000, logging.INFO)
    master.run()
