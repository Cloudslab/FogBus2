import logging
import threading
from threading import Lock
from queue import Queue
from logger import get_logger
from datatype import Worker, User, NodeSpecs
from typing import NoReturn
from datatype import Client
from collections import defaultdict
from queue import Empty
from exceptions import *
from time import sleep, time
from message import Message
from secrets import token_urlsafe


class Registry:

    def __init__(self, logLevel=logging.DEBUG):
        self.__currentWorkerID: int = 0
        self.__lockCurrentWorkerID: Lock = Lock()
        self.workers: dict[int, Worker] = {}
        self.__currentUserID: int = 0
        self.__lockCurrentUserID: Lock = Lock()
        self.users: dict[int, User] = {}
        self.clientBySocketID: dict[int, Client] = {}
        self.workerBrokerQueue: Queue[Worker] = Queue()
        self.workerByToken: dict[str, Worker] = {}

        self.workersQueueByAppID: dict[int, Queue[Worker]] = defaultdict(Queue[Worker])
        self.logger = get_logger('Master-Registry', logLevel)

    def register(self, client: Client, message: dict) -> User or Worker:
        role = message['role']
        if role == 'user':
            return self.__addUser(client, message)
        elif role == 'worker':
            return self.__addWorker(client, message)

    def __addWorker(self, client: Client, message: dict) -> Worker:
        nodeSpecs: NodeSpecs = message['nodeSpecs']
        self.__lockCurrentWorkerID.acquire()
        self.__currentWorkerID += 1
        workerID = self.__currentWorkerID
        self.__lockCurrentWorkerID.release()
        worker = Worker(
            socketID=client.socketID,
            socket_=client.socket,
            sendingQueue=client.sendingQueue,
            receivingQueue=client.receivingQueue,
            workerID=workerID,
            specs=nodeSpecs
        )

        userID = message['userID']
        appID = message['appID']
        token = message['token']

        if userID is not None \
                and userID in self.users:
            user = self.users[userID]
            isWorkerValid = user.verifyWorker(
                appID=appID,
                token=token,
                worker=worker
            )
            if not isWorkerValid:
                self.removeClient(
                    worker,
                    reason='credential is not valid')
                raise WorkerCredentialNotValid
            worker.ip = message['ip']
            worker.port = message['port']
            worker.token = token
            self.workerByToken[worker.token] = worker
            self.logger.info("Worker-%d added. %s", workerID, worker.specs.info())
        else:
            self.workerBrokerQueue.put(worker)
            self.logger.info("Worker-%d-Broker added. %s", workerID, worker.specs.info())

        self.workers[workerID] = worker
        self.clientBySocketID[client.socketID] = worker

        return worker

    def workerWait(self, worker: Worker, appID: int = None) -> NoReturn:
        self.workersQueueByAppID[appID].put(worker)

    def __workerFree(self):
        # TODO
        pass

    def __workerWork(self, appID: int, user: User):
        try:
            while True:
                worker = self.workersQueueByAppID[appID].get(block=False)
                if not worker.active:
                    continue
                worker.userByAppID[appID] = user
                user.workerByAppID[appID] = worker
                break
        except Empty:
            for _, worker in user.workerByAppID.items():
                del worker.userByAppID[appID]
            raise NoWorkerAvailableException

    def removeWorker(self, workerID) -> NoReturn:
        self.workers[workerID].active = False

    def __newUserID(self):
        self.__lockCurrentUserID.acquire()
        self.__currentUserID += 1
        userID = self.__currentUserID
        self.__lockCurrentUserID.release()
        return userID

    def __addUser(self, client: Client, message: dict):
        userID = self.__newUserID()
        appIDs = message['appIDs']

        user = User(socketID=client.socketID,
                    socket_=client.socket,
                    receivingQueue=client.receivingQueue,
                    sendingQueue=client.sendingQueue,
                    userID=userID,
                    appRunMode=message['mode'],
                    appIDs=appIDs
                    )
        threading.Thread(
            target=self.__assignWorkerForUser,
            args=(user,)).start()
        self.clientBySocketID[user.socketID] = user
        self.users[user.userID] = user
        return user

    def __assignWorkerForUser(self, user: User):
        for appID in user.appIDs:
            token = token_urlsafe(16)
            user.appIDTokenMap[appID] = token

        for i, appID in enumerate(user.appIDs):
            worker = self.workerBrokerQueue.get(timeout=1)
            token = user.appIDTokenMap[appID]
            nextWorkerToken = None if i + 1 == len(user.appIDs) \
                else user.appIDTokenMap[user.appIDs[i + 1]]
            message = {
                'type': 'runWorker',
                'userID': user.userID,
                'appID': appID,
                'token': token,
                'nextWorkerToken': nextWorkerToken}
            print(message)
            worker.sendingQueue.put(Message.encrypt(message))
            self.workerBrokerQueue.put(worker)
        self.logger.debug('Waiting for workers of userID-%d ...', user.userID)
        timestamp = time()
        while time() - timestamp < 5:
            sleep(0.1)
        message = {}
        if user.isReady:
            message['type'] = 'registration'
            message['userID'] = user.userID
            self.users[user.userID] = user
            self.clientBySocketID[user.socketID] = user
            user.sendingQueue.put(Message.encrypt(message))
            self.logger.info("User-%d added.", user.userID)
        else:
            self.logger.info("Cannot run workers for User-%d.", user.userID)
            self.removeClient(user, reason='No Enough Available Workers')

    def removeClient(self, client: Client, reason: str = None):
        message = {
            'type': 'refused',
            'reason': reason
        }

        client.sendingQueue.put(Message.encrypt(message))
        client.socket.close()

        if isinstance(client, User) \
                and client.userID in self.users:
            del self.users[client.userID]
        elif isinstance(client, Worker) \
                and client.workerID in self.workers:
            del self.workers[client.workerID]
            if client.token is not None \
                    and client.token in self.workerByToken:
                del self.workerByToken[client.token]
        if client.socketID in self.clientBySocketID:
            del self.clientBySocketID[client.socketID]
        sleep(1)
        del client
