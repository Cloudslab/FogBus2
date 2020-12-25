import logging
import socketio

from queue import Queue
from logger import get_logger
from datatype import Worker, User, NodeSpecs
from typing import NoReturn


class Registry:

    def __init__(self, logLevel=logging.DEBUG):
        self.currentWorkerID: int = 0
        self.workers: dict[int, Worker] = {}
        self.currentUserID: int = 0
        self.users: dict[int, User] = {}
        self.waitingWorkers: Queue[Worker] = Queue()
        self.logger = get_logger('Master-Registry', logLevel)

    def addWorker(self, workerSocketID: str, nodeSpecs: NodeSpecs):
        # TODO: racing
        self.currentWorkerID += 1
        workerID = self.currentWorkerID
        worker = Worker(workerID, workerSocketID, nodeSpecs)
        self.workers[workerID] = worker
        self.workerWait(worker)
        self.logger.info("Worker-%d added. %s", workerID, worker.specs.info())
        return workerID

    def workerWait(self, worker: Worker) -> NoReturn:
        self.waitingWorkers.put(worker)

    def workerWork(self) -> Worker:
        return self.waitingWorkers.get()

    def workerFree(self, worker: Worker):
        self.waitingWorkers.put(worker)

    def removeWorker(self, workerID):
        del self.workers[workerID]

    def addUser(self, registrySocketID: str):
        # TODO: racing
        self.currentUserID += 1
        userID = self.currentUserID
        user = User(userID=userID, registrySocketID=registrySocketID)
        self.users[userID] = user
        self.logger.info("User-%d added.", userID)
        return userID

    def removeUser(self, userID):
        del self.users[userID]
