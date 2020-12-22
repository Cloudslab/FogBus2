import logging
import socketio

from logger import get_logger
from datatype import Worker, User, NodeSpecs
from message import Message


class Registry:

    def __init__(self):
        self.currentWorkerID = 0
        self.workersByID = {}
        self.workersBySocketID = {}
        self.currentUserID = 0
        self.usersByID = {}
        self.usersBySocketID = {}

    def addWorker(self, socketID: str, nodeSpecs: NodeSpecs):
        self.currentWorkerID += 1
        worker = Worker(self.currentWorkerID, socketID, nodeSpecs)
        self.workersByID[self.currentWorkerID] = worker
        self.workersBySocketID[socketID] = worker
        return self.currentWorkerID

    def removeWorkerByID(self, workerID):
        del self.workersBySocketID[self.workersByID[workerID].socketID]
        del self.workersByID[workerID]

    def removeWorkerBySocketID(self, socketID):
        del self.workersByID[self.workersBySocketID[socketID].workerID]
        del self.workersBySocketID[socketID]

    def addUser(self, socketID: str):
        self.currentUserID += 1
        user = User(self.currentUserID, socketID)
        self.usersByID[self.currentUserID] = user
        self.usersBySocketID[socketID] = user
        return self.currentUserID

    def removeUserByID(self, userID):
        del self.usersBySocketID[self.usersByID[userID].socketID]
        del self.usersByID[userID]

    def removeUserBySocketID(self, socketID):
        del self.usersByID[self.usersBySocketID[socketID].userID]
        del self.usersBySocketID[socketID]


class RegistryNamespace(socketio.Namespace):

    def __init__(self, namespace=None, registry=None, sio=None, logLevel=logging.DEBUG):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.registry = registry
        self.logger = get_logger("Registry", logLevel)
        self.sio = sio

    def on_register(self, socketID, msg):
        data = Message.decrypt(msg)
        role = data["role"]
        if role == "user":
            userID = self.registry.addUser(socketID)
            self.logger.info("[*] User-%d joined.", userID)
        elif role == "worker":
            nodeSpecs = data["nodeSpecs"]
            workerID = self.registry.addWorker(socketID, nodeSpecs)
            self.logger.info("[*] Worker-%d joined: \n%s",
                             workerID, nodeSpecs.info())

    def on_exit(self, socketID):
        if socketID in self.registry.usersBySocketID:
            self.logger.info("[*] User-%d exited.", self.registry.usersBySocketID[socketID].userID)
            self.registry.removeUserBySocketID(socketID)
        else:
            self.logger.info("[*] Worker-%d exited.", self.registry.workersBySocketID[socketID].workerID)
            self.registry.removeWorkerBySocketID(socketID)

