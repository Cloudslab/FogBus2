import threading
from queue import Queue
from typing import List, Dict, Tuple
from secrets import token_urlsafe


class Client:

    def __init__(
            self,
            name: str,
            nameLogPrinting: str,
            nameConsistent: str,
            addr: Tuple[str, int],
            machineID: str):
        self.name: str = name
        self.nameLogPrinting: str = nameLogPrinting
        self.nameConsistent: str = nameConsistent
        self.addr = addr
        self.machineID: str = machineID


class Worker(Client):

    def __init__(
            self,
            machineID: str,
            addr,
            name: str,
            nameLogPrinting: str,
            nameConsistent: str,
            workerID: int):
        # TODO Containers info
        if name is None:
            name = "Worker-%d" % workerID
        super(Worker, self).__init__(
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=addr,
            machineID=machineID)

        self.id: int = workerID


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
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=addr,
            machineID=machineID)
        self.id: int = taskHandlerID
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
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=addr,
            machineID=machineID)
        self.id = userID
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
