import socket
import threading
from queue import Queue
from typing import List, Dict
from abc import abstractmethod
from time import time, sleep
from secrets import token_urlsafe
from connection import Connection


class Client:

    def __init__(
            self,
            name: str,
            addr
    ):
        self.name: str = name
        self.addr = addr


class Master:

    def __init__(self, host: str, port: int, masterID: int = 0):
        self.host = host
        self.port = port
        self.masterID = masterID


class Worker(Client):

    def __init__(
            self,
            addr,
            name: str,
            workerID: int,
    ):
        # TODO Containers info
        if name is None:
            name = "Worker-%d" % workerID
        super(Worker, self).__init__(
            name=name,
            addr=addr
        )

        self.id: int = workerID


class TaskHandler(Client):

    def __init__(
            self,
            addr,
            taskHandlerID: int,
            taskName: str,
            token: str,
            runningOnWorker: str,
            user,
            name: str = None,
    ):
        if name is None:
            name = 'TaskHandler-%d@%s@%s' % (taskHandlerID, taskName, runningOnWorker)
        super(TaskHandler, self).__init__(
            name=name,
            addr=addr,
        )

        self.id: int = taskHandlerID
        self.taskName = taskName
        self.token = token
        self.runningOnWorker: str = runningOnWorker
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
            addr,
            userID: int,
            appName: int,
            name: str,
            taskHandlerByTaskName: dict[int, Worker] = None,
    ):
        if name is None:
            name = 'User-%d' % userID
        super(User, self).__init__(
            name=name,
            addr=addr
        )
        self.id = userID
        self.appName = appName
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
