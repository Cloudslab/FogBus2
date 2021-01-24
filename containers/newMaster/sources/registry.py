from threading import Lock
from queue import Queue
from datatype import Worker, User
from datatype import TaskHandler
from connection import Message
from typing import Dict, Union, List, Tuple
from dependencies import loadDependencies, Application
from scheduling import Scheduler, Decision

Address = Tuple[str, int]


class Registry:

    def __init__(
            self,
            scheduler: Scheduler):
        self.__currentWorkerID: int = 0
        self.__lockCurrentWorkerID: Lock = Lock()
        self.__currentTaskHandlerID: int = 0
        self.__lockCurrentTaskHandlerID: Lock = Lock()
        self.workers: Dict[int, Worker] = {}
        self.__currentUserID: int = 0
        self.__lockCurrentUserID: Lock = Lock()
        self.clients: Dict[str, Union[User, Worker, TaskHandler]] = {}
        self.users: Dict[int, User] = {}
        self.workersQueue: Queue[Worker] = Queue()
        self.taskHandlerByToken: Dict[str, TaskHandler] = {}

        self.taskHandlers: Dict[int, TaskHandler] = {}

        self.profiler = self.__loadProfilers()
        self.tasks, self.applications = self.profiler
        self.messageForWorker: Queue[tuple[Dict, tuple[str, int]]] = Queue()
        self.scheduler: Scheduler = scheduler

    @staticmethod
    def __loadProfilers():
        tasks, applications = loadDependencies()
        return tasks, applications

    @staticmethod
    def __loadDependencies():
        return loadDependencies()

    def register(self, message: Message):
        targetRole = message.content['role']
        if targetRole == 'user':
            return self.__addUser(message)
        if targetRole == 'worker':
            return self.__addWorker(message)
        if targetRole == 'TaskHandler':
            return self.__addTaskHandler(message)

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

        name = 'Worker'
        nameLogPrinting = '%s-%d' % (name, workerID)
        nameConsistent = '%s#%s' % (name, machineID)
        worker = Worker(
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=message.source.addr,
            workerID=workerID,
            machineID=machineID)

        self.workers[workerID] = worker
        self.clients[worker.machineID] = worker
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
        self.clients[user.machineID] = user
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
        self.clients[taskHandler.machineID] = taskHandler
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

        self.__schedule(user)

    def __schedule(self, user):
        messageForWorkers = []
        try:
            # TODO
            decision = self.scheduler.schedule(
                applicationName=user.appName,
                label=user.label,
                userMachineID=user.machineID)
            messageForWorkers = self.__parseDecision(decision, user)
        except (KeyError, TypeError):
            # has not seen this user or
            # this is the first time fot this user
            # to request the app
            import traceback
            traceback.print_exc()
            messageForWorkers = self.__randomlySchedule(user)
        for message, addr in messageForWorkers:
            self.messageForWorker.put((message, addr))

    def __parseDecision(self, decision: Decision, user: User):
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
                worker = self.clients[machineID]
                messageForWorkers.append((message, worker.addr))
        return messageForWorkers

    def __randomlySchedule(self, user) -> List[Tuple[Dict, Address]]:

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
            messageForWorkers.append((message, worker.addr))
            self.workersQueue.put(worker)
        return messageForWorkers
