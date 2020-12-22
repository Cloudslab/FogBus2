import logging
import socketio

from queue import Queue
from logger import get_logger
from datatype import Worker, User, NodeSpecs
from message import Message
from typing import NoReturn


class Registry:

    def __init__(self):
        self.currentWorkerID = 0
        self.workersByWorkerID: {Worker} = {}
        self.workersBySocketID: {Worker} = {}
        self.currentUserID = 0
        self.usersByUserID: {User} = {}
        self.usersBySocketID: {User} = {}
        self.waitingWorkers = Queue()

    def addWorker(self, socketID: str, nodeSpecs: NodeSpecs):
        # TODO: racing
        self.currentWorkerID += 1

        workerID = self.currentWorkerID
        worker = Worker(workerID, socketID, nodeSpecs)
        self.workersByWorkerID[workerID] = worker
        self.workersBySocketID[socketID] = worker
        self.workerWait(workerID)
        return workerID

    def workerWait(self, workerID: int) -> NoReturn:
        self.waitingWorkers.put(workerID)

    def workerWork(self) -> Worker:
        return self.waitingWorkers.get(block=False)

    def removeWorkerByID(self, workerID):
        del self.workersBySocketID[self.workersByWorkerID[workerID].socketID]
        del self.workersByWorkerID[workerID]

    def removeWorkerBySocketID(self, socketID):
        del self.workersByWorkerID[self.workersBySocketID[socketID].workerID]
        del self.workersBySocketID[socketID]

    def addUser(self, socketID: str):
        self.currentUserID += 1
        user = User(self.currentUserID, socketID)
        self.usersByUserID[self.currentUserID] = user
        self.usersBySocketID[socketID] = user
        return self.currentUserID

    def removeUserByID(self, userID):
        del self.usersBySocketID[self.usersByUserID[userID].socketID]
        del self.usersByUserID[userID]

    def removeUserBySocketID(self, socketID):
        del self.usersByUserID[self.usersBySocketID[socketID].userID]
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
