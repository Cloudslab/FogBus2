import threading
from queue import Queue
from typing import List, Dict, Tuple
from secrets import token_urlsafe
from node import Identity
from resourcesInfo import ResourcesInfo, ImagesAndContainers

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
            resources: ResourcesInfo):
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
        self.resources: ResourcesInfo = resources


class TaskHandler(Client):

    def __init__(
            self,
            machineID: str,
            addr,
            taskHandlerID: int,
            taskName: str,
            token: str,
            worker: Worker,
            user,
            name: str,
            nameLogPrinting: str,
            nameConsistent: str):
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
            taskHandlerByTaskName: dict[int, Worker] = None,
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
        self.entranceTasksByName: List[str] = []
        self.respondMessageQueue: Queue = Queue()
        self.lock: threading.Lock = threading.Lock()
        self.isReady = False

    def generateToken(self, taskName: str):
        token = token_urlsafe(16)
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
