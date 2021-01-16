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

from dependencies import loadDependencies, Application, Task, Dependency
from weights import loadEdgeWeights, loadTaskWeights


class Registry:

    def __init__(
            self,
            logLevel=logging.DEBUG):
        self.__currentWorkerID: int = 0
        self.__lockCurrentWorkerID: Lock = Lock()
        self.workers: dict[int, Worker] = {}
        self.__currentUserID: int = 0
        self.__lockCurrentUserID: Lock = Lock()
        self.users: dict[int, User] = {}
        self.clientBySocketID: dict[int, Client] = {}
        self.workerBrokerQueue: Queue[Worker] = Queue()
        self.workerByToken: dict[str, Worker] = {}

        self.profiler = self.__loadProfilers()
        self.tasks, self.applications, self.edgeWeights, self.taskWeights = self.profiler
        self.logger = get_logger('Master-Registry', logLevel)

    @staticmethod
    def __loadProfilers():
        tasks, applications = loadDependencies()
        edgeWeights = loadEdgeWeights(applications)
        taskWeights = loadTaskWeights(tasks, applications)
        return tasks, applications, edgeWeights, taskWeights

    @staticmethod
    def __loadDependencies():
        return loadDependencies()

    def __scaleMethod(self):
        # TODO
        pass

    def __scheduleMethod(self):
        # TODO
        # 1. Input: Consider user requests
        # 2. Resources / Workers
        # 3. Applications
        #
        # some algorithm here
        #
        # return the decision

        pass

    def __grabWorkersInfo(self):
        # TODO
        # List of workers
        pass

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

        userID = message['userID']
        taskName = message['taskName']
        token = message['token']
        ownedBy = message['ownedBy']

        worker = Worker(
            socketID=client.socketID,
            socket_=client.socket,
            sendingQueue=client.sendingQueue,
            receivingQueue=client.receivingQueue,
            workerID=workerID,
            specs=nodeSpecs,
            ownedBy=ownedBy,
            connectionIO=client.connectionIO
        )

        if userID is not None \
                and userID in self.users:
            user = self.users[userID]
            isWorkerValid = user.verifyWorker(
                taskName=taskName,
                token=token,
                worker=worker
            )
            if not isWorkerValid:
                self.removeClient(worker)
                raise WorkerCredentialNotValid
            worker.ip = worker.socket.getsockname()[0]
            worker.port = message['port']
            worker.token = token
            self.workerByToken[worker.token] = worker
            taskName = message['taskName']
            worker.name = "Worker-%d-Task-%d-%s@%s" % (workerID, ownedBy, taskName, user.name)
            self.logger.info("%s added. %s", worker.name, worker.specs.info())
        else:
            self.workerBrokerQueue.put(worker)
            worker.name = "Worker-%d-Broker" % workerID
            self.logger.info("Worker-%d-Broker added. %s", workerID, worker.specs.info())

        self.workers[workerID] = worker
        self.clientBySocketID[client.socketID] = worker

        return worker


    def __newUserID(self):
        self.__lockCurrentUserID.acquire()
        self.__currentUserID += 1
        userID = self.__currentUserID
        self.__lockCurrentUserID.release()
        return userID

    def __addUser(self, client: Client, message: dict):
        userID = self.__newUserID()
        appName = message['appName']
        label = message['label']
        user = User(
            socketID=client.socketID,
            socket_=client.socket,
            receivingQueue=client.receivingQueue,
            sendingQueue=client.sendingQueue,
            userID=userID,
            appRunMode=message['mode'],
            appName=appName,
            connectionIO=client.connectionIO
        )
        user.name = '%s@User-%d' % (label, user.userID)
        # threading.Thread(
        #     target=self.__handleForUserRequest,
        #     args=(user,)).start()
        self.clientBySocketID[user.socketID] = user
        self.users[user.userID] = user
        return self.__handleForUserRequest(user)

    def __schedule(self, user):
        for taskName, userTask in user.taskNameTokenMap.items():
            token = userTask.token
            childTaskTokens = userTask.childTaskTokens
            worker = self.workerBrokerQueue.get(timeout=1)
            message = {
                'type': 'runWorker',
                'userID': user.userID,
                'userName': user.name,
                'taskName': taskName,
                'token': token,
                'childTaskTokens': childTaskTokens}
            worker.sendingQueue.put(Message.encrypt(message))
            self.workerBrokerQueue.put(worker)

    def __handleForUserRequest(self, user: User):

        app: Application = self.applications[user.appName]

        for taskName, dependency in app.dependencies.items():
            if taskName in ['Sensor', 'Actor', 'RemoteLogger']:
                if taskName == 'Sensor':
                    user.entranceTasksByName = dependency.childTaskList
                continue
            user.generateToken(taskName)

        for taskName, dependency in app.dependencies.items():
            if taskName in ['Sensor', 'Actor', 'RemoteLogger']:
                continue
            childTaskTokens = []
            for childTaskName in dependency.childTaskList:
                if childTaskName in ['Sensor', 'Actor', 'RemoteLogger']:
                    continue
                childTaskTokens.append(user.taskNameTokenMap[childTaskName].token)
            user.taskNameTokenMap[taskName].childTaskTokens = childTaskTokens

        self.__schedule(user)

        self.logger.debug('Waiting for workers of userID-%d ...', user.userID)
        timestamp = time()
        while time() - timestamp < 5 and not user.isReady:
            sleep(0.1)
        if user.isReady:
            message = {
                'type': 'registration',
                'userID': user.userID}
            self.users[user.userID] = user
            self.clientBySocketID[user.socketID] = user
            user.sendingQueue.put(Message.encrypt(message))
            self.logger.info("User-%d added.", user.userID)
        else:
            self.logger.info("Cannot run workers for User-%d.", user.userID)
            self.removeClient(user)
        return user

    def removeClient(self, client: Client):
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
