import threading
from queue import Queue
from typing import List, Dict, Tuple, Set
from secrets import token_hex
from node import Identity
from time import time

Address = Tuple[str, int]


class Client(Identity):
    pass


class Worker(Client):

    def __init__(
            self,
            machineID: str,
            addr,
            name: str,
            nameLogPrinting: str,
            nameConsistent: str,
            workerID: int,
            systemCPUUsage: int,
            cpuUsage: int,
            memoryUsage: int,
            peekMemoryUsage: int,
            maxMemory: int,
            totalCPUCores: int,
            cpuFreq: float,
            images: Set[str]):
        # TODO Containers info
        if name is None:
            name = "Worker-%d" % workerID
        super(Worker, self).__init__(
            id_=workerID,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=addr,
            machineID=machineID)
        self.systemCPUUsage = systemCPUUsage
        self.cpuUsage = cpuUsage
        self.memoryUsage = memoryUsage
        self.peekMemoryUsage = peekMemoryUsage
        self.maxMemory = maxMemory
        self.totalCPUCores = totalCPUCores
        self.cpuFreq = cpuFreq
        self.images: Set[str] = images


class TaskHandler(Client):

    def __init__(
            self,
            addr,
            taskHandlerID: int,
            taskName: str,
            token: str,
            worker: Worker,
            user,
            name: str,
            nameLogPrinting: str,
            nameConsistent: str,
            machineID: str = None):
        super(TaskHandler, self).__init__(
            id_=taskHandlerID,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=addr,
            machineID=machineID)
        self.taskName = taskName
        self.token = token
        self.worker: Worker = worker
        self.user: User = user
        self.ready: threading.Event = threading.Event()


class UserTask:
    def __init__(self, token: str, childTaskTokens=None):
        if childTaskTokens is None:
            childTaskTokens = []
        self.token: str = token
        self.childTaskTokens: List[str] = childTaskTokens


class User(Client):

    def __init__(
            self,
            machineID: str,
            addr,
            userID: int,
            appName: str,
            label: str,
            name: str,
            nameLogPrinting: str,
            nameConsistent: str,
            taskHandlerByTaskName: dict[str, TaskHandler] = None,
    ):
        if name is None:
            name = 'User-%d' % userID
        super(User, self).__init__(
            id_=userID,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=addr,
            machineID=machineID)
        self.appName: str = appName
        self.label: str = label
        self.taskNameTokenMap: Dict[str, UserTask] = {}
        if taskHandlerByTaskName is None:
            self.taskHandlerByTaskName: dict[str, TaskHandler] = {}
            self.notReadyTasks = set([])
            self.lastTaskReadyTime = time()
        self.entranceTasksByName: List[str] = []
        self.respondMessageQueue: Queue = Queue()
        self.lock: threading.Lock = threading.Lock()
        self.isReady = False
        self.lockCheckResource = threading.Lock()

    def generateToken(self, taskName: str):
        token = token_hex(32)
        self.taskNameTokenMap[taskName] = UserTask(
            token=token)
        return token

    def verifyTaskHandler(
            self, taskName: str,
            taskHandler: TaskHandler) -> bool:
        if taskName in self.taskNameTokenMap \
                and self.taskNameTokenMap[taskName].token == taskHandler.token:
            return True
        return False
