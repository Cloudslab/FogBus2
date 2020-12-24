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
        self.workers: {Worker} = {}
        self.currentUserID = 0
        self.users: {User} = {}
        self.waitingWorkers = Queue()
        self.logger = get_logger('MasterRegistry', logLevel)

    def addWorker(self, socketID: str, nodeSpecs: NodeSpecs):
        # TODO: racing
        self.currentWorkerID += 1
        workerID = self.currentWorkerID
        worker = Worker(workerID, socketID, nodeSpecs)
        self.workers[workerID] = worker
        self.workerWait(worker)
        self.logger.info("Worker-%d added. %s", workerID, worker.specs.info())
        return workerID

    def updateWorkerTaskSocketID(self, workerID: int, socketID: int):
        self.workers[workerID].taskSocketID = socketID
        self.logger.info("Worker-%d updated taskSocketID.", workerID)

    def workerWait(self, worker: Worker) -> NoReturn:
        self.waitingWorkers.put(worker)

    def workerWork(self) -> Worker:
        return self.waitingWorkers.get(block=False)

    def removeWorker(self, workerID):
        del self.workers[workerID]

    def addUser(self, socketID: str):
        # TODO: racing
        self.currentUserID += 1
        userID = self.currentUserID
        user = User(userID, socketID)
        self.users[userID] = user
        self.logger.info("User-%d added.", userID)
        return userID

    def updateUserTaskSocketID(self, userID: int, socketID: int):
        self.users[userID].taskSocketID = socketID
        self.logger.info("User-%d updated taskSocketID.", userID)

    def removeUser(self, userID):
        del self.users[userID]


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
            self.logger.info("[*] User-%d exited.", self.registry.usersBySocketID[socketID].workerID)
            self.registry.removeUserBySocketID(socketID)
        else:
            self.logger.info("[*] Worker-%d exited.", self.registry.workersBySocketID[socketID].workerID)
            self.registry.removeWorkerBySocketID(socketID)
