import logging
import threading

from time import sleep
from queue import Empty
from logger import get_logger
from datatype import Task, Worker
from registry import Registry
from message import Message
from dataManager import DataManager
from taskNamespace import TaskNamespace
from taskManager import TaskManager


class TaskCoordinator:

    def __init__(self,
                 registry: Registry,
                 taskNamespace: TaskNamespace,
                 taskManager: TaskManager,
                 dataManager: DataManager,
                 logLevel=logging.DEBUG):
        self.registry: Registry = registry
        self.taskNamespace: TaskNamespace = taskNamespace
        self.taskManager: TaskManager = taskManager
        self.dataManager: DataManager = dataManager
        self.logger = get_logger("Coordinator", logLevel)

    def run(self):
        t = threading.Thread(target=self.assigner)
        t.start()
        t = threading.Thread(target=self.delivery)
        t.start()

    def assigner(self):
        self.logger.info("[*] Assigner started.")
        n = 0
        while True:
            worker = None
            task = None
            try:
                worker = self.registry.workerWork()
                task = self.taskManager.getUnfinishedTask(worker.workerID)
                self.sendTask(worker, task)
            except Empty:
                if worker is not None:
                    self.registry.workerFree(worker)
                n += 1
                if n > 1000:
                    # self.logger.debug("[*] No worker or unfinished task")
                    sleep(1)
                    n = 0

    def delivery(self):
        self.logger.info("[*] Delivery started.")
        n = 0
        while True:
            try:
                task = self.taskManager.getFinishedTask()
                self.sendResult(task)
            except Empty:
                n += 1
                if n > 1000:
                    # self.logger.debug("[*] No finished task")
                    sleep(1)
                    n = 0

    def sendTask(self, worker: Worker, task: Task):
        message = {"taskID": task.taskID, "appID": task.appID, "dataID": task.dataID}
        messageEncrypted = Message.encrypt(message)
        self.taskNamespace.emit(
            'task',
            room=worker.taskSocketID,
            data=messageEncrypted,
            namespace='/task')
        self.logger.debug("Sent task %d", task.taskID)

    def sendResult(self, task: Task):
        user = self.registry.users[task.userID]
        message = {"appID": task.dataID, "dataID": task.resultID}
        messageEncrypted = Message.encrypt(message)
        self.taskNamespace.emit(
            'result',
            room=user.socketID,
            data=messageEncrypted,
            namespace='/task')
        self.logger.debug("Sent result %d", task.taskID)
