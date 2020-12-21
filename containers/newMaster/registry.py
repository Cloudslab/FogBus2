import socketio
import logging
import cv2

from logger import get_logger
from datatype import Worker, NodeSpecs
from message import Message


class Registry:

    def __init__(self):
        self.id = 0
        self.workers = {}

    def addWoker(self, sid: str, nodeSpecs: NodeSpecs):
        self.id += 1
        self.workers[self.id] = Worker(self.id, sid, nodeSpecs)
        return self.id

    def remove(self, workerID):
        del self.workers[workerID]


class RegistryNamespace(socketio.Namespace):

    def __init__(self, namespace=None, registry=None, sio=None, logLevel=logging.DEBUG, q= None):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.registry = registry
        self.logger = get_logger("Registry", logLevel)
        self.sio = sio
        self.q = q

    def on_connect(self, socketID, environ):
        pass

    def on_register(self, socketID, msg):
        nodeSpecs = Message.decrypt(msg)
        workerID = self.registry.addWoker(socketID, nodeSpecs)
        self.logger.info("[*] Worker-%d joined: \n%s" %
                         (workerID, nodeSpecs.info()))

       

    def on_finish(self, data):
        print("finished")
        frame = Message.decrypt(data)
        cv2.imwrite("?.jpg", frame)

    def on_disconnect(self, socketID):
        print('disconnect ', socketID)
