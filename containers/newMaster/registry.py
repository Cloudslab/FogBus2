import logging

from threading import Lock
from queue import Queue
from logger import get_logger
from datatype import Worker, User, NodeSpecs
from typing import NoReturn


class Registry:

    def __init__(self, logLevel=logging.DEBUG):
        self.__currentWorkerID: int = 0
        self.__lockCurrentWorkerID: Lock = Lock()
        self.workers: dict[int, Worker] = {}
        self.__currentUserID: int = 0
        self.__lockCurrentUserID: Lock = Lock()
        self.users: dict[int, User] = {}
        self.waitingWorkers: Queue[Worker] = Queue()
        self.logger = get_logger('Master-Registry', logLevel)

    def register(self, socketID: int, message: dict):
        role = message['role']
        if role == 'user':
            self.addUser(socketID)
        pass

    def __addWorker(self, workerSocketID: int, nodeSpecs: NodeSpecs):
        self.__lockCurrentWorkerID.acquire()
        self.__currentWorkerID += 1
        workerID = self.__currentWorkerID
        self.__lockCurrentWorkerID.release()
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

    def addUser(self, registrySocketID: int):
        self.__lockCurrentUserID.acquire()
        self.__currentUserID += 1
        userID = self.__currentUserID
        self.__lockCurrentUserID.release()
        user = User(userID=userID, socketID=registrySocketID)
        self.users[userID] = user
        self.logger.info("User-%d added.", userID)
        return userID

    def removeUser(self, userID):
        del self.users[userID]
