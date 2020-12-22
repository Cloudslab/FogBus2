import socketio
import logging
import cv2

from logger import get_logger
from datatype import Worker, NodeSpecs
from message import Message


class Registry:

    def __init__(self):
        self.id = 0
        self.workersByID = {}
        self.workersBySocketID = {}

    def addWoker(self, socketID: str, nodeSpecs: NodeSpecs):
        self.id += 1
        worker = Worker(self.id, socketID, nodeSpecs)
        self.workersByID[self.id] = worker
        self.workersBySocketID[socketID] = worker
        return self.id

    def removeByID(self, workerID):
        del self.workersBySocketID[self.workersByID[workerID].socketID]
        del self.workersByID[workerID]

    def removeBySocketID(self, socketID):
        del self.workersByID[self.workersBySocketID[socketID].workerID]
        del self.workersBySocketID[socketID]


class RegistryNamespace(socketio.Namespace):

    def __init__(self, namespace=None, registry=None, sio=None, logLevel=logging.DEBUG):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.registry = registry
        self.logger = get_logger("Registry", logLevel)
        self.sio = sio

    def on_connect(self, socketID, environ):
        pass

    def on_register(self, socketID, msg):
        nodeSpecs = Message.decrypt(msg)
        workerID = self.registry.addWoker(socketID, nodeSpecs)
        self.logger.info("[*] Worker-%d joined: \n%s",
                         workerID, nodeSpecs.info())

    def on_disconnect(self, socketID):
        self.registry.removeBySocketID(socketID)
        print('disconnect ', socketID)
