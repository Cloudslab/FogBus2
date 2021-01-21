import logging
from threading import Lock
from queue import Queue
from logger import get_logger
from datatype import Worker, User, NodeSpecs, ConnectionIO
from datatype import Client, TaskHandler
from exceptions import *
from time import sleep, time
from connection import Message, Connection

from typing import Dict
from dependencies import loadDependencies, Application, Task, Dependency
from weights import loadEdgeWeights, loadTaskWeights


class Registry:

    def __init__(
            self,
            logLevel=logging.DEBUG):
        self.__currentWorkerID: int = 0
        self.__lockCurrentWorkerID: Lock = Lock()
        self.__currentTaskHandlerID: int = 0
        self.__lockCurrentTaskHandlerID: Lock = Lock()
        self.workers: dict[int, Worker] = {}
        self.__currentUserID: int = 0
        self.__lockCurrentUserID: Lock = Lock()
        self.users: dict[int, User] = {}
        self.clientBySocketID: dict[int, Client] = {}
        self.workersQueue: Queue[Worker] = Queue()
        self.taskHandlerByToken: dict[str, TaskHandler] = {}

        self.taskHandlers: Dict[int, TaskHandler] = {}

        self.profiler = self.__loadProfilers()
        self.tasks, self.applications, self.edgeWeights, self.taskWeights = self.profiler
        self.logger = get_logger('Master-Registry', logLevel)
        self.messageForWorker: Queue[tuple[Dict, tuple[str, int]]] = Queue()

    @staticmethod
    def __loadProfilers():
        tasks, applications = loadDependencies()
        edgeWeights = loadEdgeWeights(applications)
        taskWeights = loadTaskWeights(tasks, applications)
        return tasks, applications, edgeWeights, taskWeights

    @staticmethod
    def __loadDependencies():
        return loadDependencies()

    def register(self, message: Message):
        targetRole = message.content['role']
        if targetRole == 'user':
            return self.__addUser(message, message.source.addr)
        if targetRole == 'worker':
            return self.__addWorker(message, message.source.addr)
        if targetRole == 'taskHandler':
            return self.__addTaskHandler(message, message.source.addr)

    def __newWorkerID(self):
        self.__lockCurrentWorkerID.acquire()
        self.__currentWorkerID += 1
        workerID = self.__currentWorkerID
        self.__lockCurrentWorkerID.release()
        return workerID

    def __addWorker(self, message: Message, addr):
        workerID = self.__newWorkerID()

        worker = Worker(
            name='Worker-%d' % workerID,
            addr=addr,
            workerID=workerID,
            connectionIO=ConnectionIO()
        )

        self.workers[workerID] = worker
        respond = {
            'type': 'registered',
            'role': 'worker',
            'name': worker.name,
            'id': workerID
        }

        self.workersQueue.put(worker)
        return respond

    def __newTaskID(self):
        self.__lockCurrentTaskHandlerID.acquire()
        self.__currentTaskHandlerID += 1
        taskHandlerID = self.__currentTaskHandlerID
        self.__lockCurrentTaskHandlerID.release()
        return taskHandlerID

    def __addTaskHandler(self, message: Message, addr):
        taskHandlerID = self.__newTaskID()

        userID = message.content['userID']
        taskName = message.content['taskName']
        token = message.content['token']
        runningOnWorker = message.content['runningOnWorker']
        user = self.users[userID]

        taskHandler = TaskHandler(
            taskHandlerID=taskHandlerID,
            addr=addr,
            token=token,
            taskName=taskName,
            runningOnWorker=runningOnWorker,
            connectionIO=ConnectionIO(),
            user=user
        )

        isTaskValid = user.verifyTaskHandler(
            taskName=taskName,
            taskHandler=taskHandler
        )
        if not isTaskValid:
            respond = {
                'type': 'disconnect',
                'reason': 'token is not valid'
            }
            return respond

        self.taskHandlers[taskHandler.id] = taskHandler
        self.taskHandlerByToken[taskHandler.token] = taskHandler
        respond = {
            'type': 'registered',
            'role': 'taskHandler',
            'id': taskHandlerID,
            'name': taskHandler.name,
        }
        return respond

    def __newUserID(self):
        self.__lockCurrentUserID.acquire()
        self.__currentUserID += 1
        userID = self.__currentUserID
        self.__lockCurrentUserID.release()
        return userID

    def __addUser(self, message: Message, addr):
        userID = self.__newUserID()
        appName = message.content['appName']
        label = message.content['label']

        user = User(
            name='%s@%s@User-%d' % (appName, label, userID),
            addr=addr,
            userID=userID,
            appName=appName,
            connectionIO=ConnectionIO()
        )
        self.users[user.id] = user
        self.__handleRequest(user)
        respond = {
            'type': 'registered',
            'role': 'user',
            'id': userID,
            'name': user.name
        }
        return respond

    def __schedule(self, user):
        for taskName, userTask in user.taskNameTokenMap.items():
            token = userTask.token
            childTaskTokens = userTask.childTaskTokens
            # Scheduling Algorithm
            worker = self.workersQueue.get(timeout=1)
            message = {
                'type': 'runTaskHandler',
                'userID': user.id,
                'userName': user.name,
                'taskName': taskName,
                'token': token,
                'childTaskTokens': childTaskTokens, }
            self.messageForWorker.put((message, worker.addr))
            self.workersQueue.put(worker)

    def __handleRequest(self, user: User):

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
