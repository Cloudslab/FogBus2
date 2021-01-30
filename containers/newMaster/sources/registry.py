import logging
import os
from abc import ABC
from threading import Lock
from node import Node
from profilerManage import Profiler
from queue import Queue
from datatype import Worker, User, TaskHandler
from connection import Message
from typing import Dict, Union, List, Tuple
from dependencies import loadDependencies, Application
from scheduling import Scheduler, Decision, NSGA3, NSGA2, CTAEA
from collections import defaultdict

Address = Tuple[str, int]


class Registry(Profiler, Node, ABC):

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
            ignoreSocketErr: bool,
            schedulerName: str,
            logLevel=logging.DEBUG):
        Profiler.__init__(self)
        Node.__init__(
            self,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            ignoreSocketErr=ignoreSocketErr,
            periodicTasks=[
                (self._saveToPersistentStorage, 2),
                (self.__requestProfiler, 1)],
            logLevel=logLevel
        )
        self.__currentWorkerID: int = 0
        self.__lockCurrentWorkerID: Lock = Lock()
        self.__currentTaskHandlerID: int = 0
        self.__lockCurrentTaskHandlerID: Lock = Lock()
        self.workers: Dict[Union[int, str], Worker] = {}
        self.__currentUserID: int = 0
        self.__lockCurrentUserID: Lock = Lock()
        self.users: Dict[int, User] = {}
        self.workersQueue: Queue[Worker] = Queue()
        self.taskHandlerByToken: Dict[str, TaskHandler] = {}

        self.taskHandlers: Dict[int, TaskHandler] = {}

        self.profiler = self.__loadProfilers()
        self.tasks, self.applications = self.profiler
        self.scheduler: Scheduler = self.__getScheduler(
            schedulerName=schedulerName)
        self.logger = None

    @staticmethod
    def __loadProfilers():
        tasks, applications = loadDependencies()
        return tasks, applications

    @staticmethod
    def __loadDependencies():
        return loadDependencies()

    def __getScheduler(self, schedulerName: str) -> Scheduler:
        if schedulerName in {None, 'NSGA3'}:
            return NSGA3(
                averagePackageSize=self.averagePackageSize,
                averageDelay=self.averageDelay,
                averageProcessTime=self.averageProcessTime,
                populationSize=10,
                generationNum=100,
                dasDennisP=1)
        elif schedulerName == 'NSGA2':
            return NSGA2(
                averagePackageSize=self.averagePackageSize,
                averageDelay=self.averageDelay,
                averageProcessTime=self.averageProcessTime,
                populationSize=10,
                generationNum=100)
        elif schedulerName == 'CTAEA':
            return CTAEA(
                averagePackageSize=self.averagePackageSize,
                averageDelay=self.averageDelay,
                averageProcessTime=self.averageProcessTime,
                generationNum=100,
                dasDennisP=1)
        self.logger.warning('Unknown scheduler: %s', schedulerName)
        os._exit(0)

    def registerClient(self, message: Message):
        targetRole = message.content['role']
        if targetRole == 'user':
            return self.__addUser(message)
        if targetRole == 'worker':
            return self.__addWorker(message)
        if targetRole == 'TaskHandler':
            return self.__addTaskHandler(message)
        return None

    def __newWorkerID(self):
        self.__lockCurrentWorkerID.acquire()
        self.__currentWorkerID += 1
        workerID = self.__currentWorkerID
        self.__lockCurrentWorkerID.release()
        return workerID

    def __newUserID(self):
        self.__lockCurrentUserID.acquire()
        self.__currentUserID += 1
        userID = self.__currentUserID
        self.__lockCurrentUserID.release()
        return userID

    def __newTaskID(self):
        self.__lockCurrentTaskHandlerID.acquire()
        self.__currentTaskHandlerID += 1
        taskHandlerID = self.__currentTaskHandlerID
        self.__lockCurrentTaskHandlerID.release()
        return taskHandlerID

    def __addWorker(self, message: Message):
        workerID = self.__newWorkerID()
        machineID = message.content['machineID']
        resources = message.content['resources']

        name = 'Worker'
        nameLogPrinting = '%s-%d' % (name, workerID)
        nameConsistent = '%s#%s' % (name, machineID)
        worker = Worker(
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=message.source.addr,
            workerID=workerID,
            machineID=machineID,
            resources=resources)

        self.workers[workerID] = worker
        self.workers[worker.machineID] = worker
        respond = {
            'type': 'registered',
            'role': 'worker',
            'name': worker.name,
            'nameLogPrinting': worker.nameLogPrinting,
            'nameConsistent': worker.nameConsistent,
            'id': workerID
        }

        self.workersQueue.put(worker)
        return respond

    def __addUser(self, message: Message):
        userID = self.__newUserID()
        appName = message.content['appName']
        label = message.content['label']
        machineID = message.content['machineID']

        name = '%s@%s@User' % (appName, label)
        nameLogPrinting = '%s-%d' % (name, userID)
        nameConsistent = '%s#%s' % (name, machineID)

        user = User(
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=message.source.addr,
            userID=userID,
            appName=appName,
            label=label,
            machineID=machineID)
        self.users[user.id] = user
        self.__handleRequest(user)
        respond = {
            'type': 'registered',
            'role': 'user',
            'id': userID,
            'name': user.name,
            'nameLogPrinting': user.nameLogPrinting,
            'nameConsistent': user.nameConsistent,
        }
        return respond

    def __addTaskHandler(self, message: Message):
        taskHandlerID = self.__newTaskID()

        userID = message.content['userID']
        taskName = message.content['taskName']
        token = message.content['token']
        workerID = message.content['workerID']

        if userID not in self.users:
            return
        if workerID not in self.workers:
            return
        user = self.users[userID]
        worker = self.workers[workerID]

        # To differentiate where this taskHandler is running on
        # Thus use worker machineID as the taskHandler machineID
        machineID = worker.machineID
        name = '%s@%s@TaskHandler' % (taskName, user.label)
        nameLogPrinting = '%s-%d' % (name, taskHandlerID)
        nameConsistent = '%s#%s' % (name, machineID)

        taskHandler = TaskHandler(
            taskHandlerID=taskHandlerID,
            addr=message.source.addr,
            token=token,
            taskName=taskName,
            worker=worker,
            user=user,
            name='%s@TaskHandler' % taskName,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            machineID=machineID)

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
            'role': 'TaskHandler',
            'id': taskHandlerID,
            'name': taskHandler.name,
            'nameLogPrinting': taskHandler.nameLogPrinting,
            'nameConsistent': taskHandler.nameConsistent,
            'workerMachineID': worker.machineID
        }
        return respond

    def __handleRequest(self, user: User):

        app: Application = self.applications[user.appName]

        skipRoles = {'Sensor', 'Actor', 'RemoteLogger'}
        for taskName, dependency in app.dependencies.items():
            if taskName in skipRoles:
                if taskName == 'Sensor':
                    user.entranceTasksByName = dependency.childTaskList
                continue
            user.generateToken(taskName)

        for taskName, dependency in app.dependencies.items():
            if taskName in skipRoles:
                continue
            childTaskTokens = []
            for childTaskName in dependency.childTaskList:
                if childTaskName in skipRoles:
                    continue
                childTaskTokens.append(user.taskNameTokenMap[childTaskName].token)
            user.taskNameTokenMap[taskName].childTaskTokens = childTaskTokens
        # import cProfile, pstats, io
        # from pstats import SortKey
        # pr = cProfile.Profile()
        # pr.enable()
        self.__schedule(user)
        # pr.disable()
        # s = io.StringIO()
        # sortby = SortKey.CUMULATIVE
        # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        # ps.print_stats()
        # print(s.getvalue())

    def __schedule(self, user):
        allWorkers = []
        workersResources = {}
        for key in self.workers.keys():
            if not isinstance(key, str):
                continue
            worker = self.workers[key]
            allWorkers.append(key)
            workersResources[key] = worker.resources
        # suppose each worker has all taskHandlers
        availableWorkers = defaultdict(lambda: allWorkers)

        decision = self.scheduler.schedule(
            userName=user.name,
            userMachine=user.machineID,
            masterName=self.nameLogPrinting,
            masterMachine=self.machineID,
            applicationName=user.appName,
            label=user.label,
            availableWorkers=availableWorkers,
            workersResources=workersResources)
        messageForWorkers = self.__parseDecision(decision, user)

        del decision.__dict__['machines']
        self.logger.info(
            'Scheduled by %s: %s' % (self.scheduler.name, decision))

        for message, worker in messageForWorkers:
            self.sendMessage(message, worker.addr)

    def __parseDecision(self, decision: Decision, user: User) -> List[Tuple[Dict, Worker]]:
        messageForWorkers = []
        for machineName, machineID in decision.machines.items():
            nameSplit = machineName.split('@')
            machineRole = nameSplit[-1]
            taskName = nameSplit[0]
            if machineRole == 'TaskHandler':
                userTask = user.taskNameTokenMap[taskName]
                message = {
                    'type': 'runTaskHandler',
                    'userID': user.id,
                    'userName': user.name,
                    'taskName': taskName,
                    'token': userTask.token,
                    'childTaskTokens': userTask.childTaskTokens}
                worker = self.workers[machineID]
                messageForWorkers.append((message, worker))
        return messageForWorkers

    def __randomlySchedule(self, user) -> List[Tuple[Dict, Worker]]:

        messageForWorkers = []
        for taskName, userTask in user.taskNameTokenMap.items():
            token = userTask.token
            childTaskTokens = userTask.childTaskTokens
            # Scheduling Algorithm
            while True:
                worker = self.workersQueue.get(timeout=1)
                if worker.id in self.workers:
                    break
            message = {
                'type': 'runTaskHandler',
                'userID': user.id,
                'userName': user.name,
                'taskName': taskName,
                'token': token,
                'childTaskTokens': childTaskTokens}
            messageForWorkers.append((message, worker))
            self.workersQueue.put(worker)
        return messageForWorkers

    def __requestProfiler(self):
        msg = {'type': 'requestProfiler'}
        self.sendMessage(msg, self.remoteLogger.addr)
