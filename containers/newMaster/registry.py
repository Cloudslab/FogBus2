import logging
import socketio

from queue import Queue
from logger import get_logger
from datatype import Worker, User, NodeSpecs
from message import Message
from typing import NoReturn


class Registry:

    def __init__(self, logLevel=logging.DEBUG):
        self.currentWorkerID = 0
        self.workersByWorkerID: {Worker} = {}
        self.workersBySocketID: {Worker} = {}
        self.currentUserID = 0
        self.usersByUserID: {User} = {}
        self.usersBySocketID: {User} = {}
        self.waitingWorkers = Queue()
        self.logger = get_logger('MasterRegistry', logLevel)

    def addWorker(self, socketID: str, nodeSpecs: NodeSpecs):
        # TODO: racing
        self.currentWorkerID += 1
        workerID = self.currentWorkerID
        worker = Worker(workerID, socketID, nodeSpecs)
        self.workersByWorkerID[workerID] = worker
        self.workersBySocketID[socketID] = worker
        self.workerWait(workerID)
        self.logger.info("Worker-%d added.", workerID)
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
        # TODO: racing
        self.currentUserID += 1
        userID = self.currentUserID
        user = User(userID, socketID)
        self.usersByUserID[userID] = user
        self.usersBySocketID[socketID] = user
        self.logger.info("User-%d added.", userID)
        return userID

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
        self.logger = get_logger("MasterRegistryNamespace", logLevel)
        self.sio = sio

    def on_register(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        role = messageDecrypted["role"]
        if role == "user":
            userID = self.registry.addUser(socketID)
            messageEncrypted = Message.encrypt(userID)
            self.emit('registered', data=messageEncrypted)
        elif role == "worker":
            nodeSpecs = messageDecrypted["nodeSpecs"]
            workerID = self.registry.addWorker(socketID, nodeSpecs)
            messageEncrypted = Message.encrypt(workerID)
            self.emit('registered', data=messageEncrypted)

    def on_exit(self, socketID):
        if socketID in self.registry.usersBySocketID:
            self.logger.info("[*] User-%d exited.", self.registry.usersBySocketID[socketID].userID)
            self.registry.removeUserBySocketID(socketID)
        else:
            self.logger.info("[*] Worker-%d exited.", self.registry.workersBySocketID[socketID].workerID)
            self.registry.removeWorkerBySocketID(socketID)
