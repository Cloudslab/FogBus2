import logging
import threading
import socketio

from time import sleep
from queue import Queue, Empty
from logger import get_logger
from datatype import Task, Worker
from registry import Registry
from message import Message
from typing import NoReturn
from dataManager import DataManager


class TaskManager:

    def __init__(self, logLevel=logging.DEBUG):
        self.currentTaskID = 0
        self.waitingTasks = Queue()
        self.finishedTasks = Queue()
        self.processingTasks: {Task} = {}
        self.logger = get_logger('TaskManager', logLevel)

    def submit(self, userID: int, appID: int, dataID: int):
        # TODO: racing
        self.currentTaskID += 1
        taskID = self.currentTaskID
        self.waitingTasks.put(
            Task(
                userID=userID,
                taskID=taskID,
                appID=appID,
                dataID=dataID))
        return taskID

    def getUnfinishedTask(self, workerID: int) -> Task:
        task = self.waitingTasks.get(block=False)
        task.workerID = workerID
        self.processingTasks[task.taskID] = task
        return task

    def getFinishedTask(self) -> Task:
        task = self.finishedTasks.get(block=False)
        return task

    def finish(self, taskID, outputData: bytes) -> NoReturn:
        if taskID in self.processingTasks:
            task = self.processingTasks[taskID]
            task.outputData = outputData
            task.hasDone = True
            self.finishedTasks.put(task)
            del self.processingTasks[taskID]


class Coordinator:

    def __init__(self,
                 registry: Registry,
                 sio: socketio.Server,
                 taskManager: TaskManager,
                 dataManager: DataManager,
                 logLevel=logging.DEBUG):
        self.registry: Registry = registry
        self.sio: socketio.Server = sio
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
            try:
                worker = self.registry.workerWork()
                task = self.taskManager.getUnfinishedTask(worker.workerID)
                self.sendTask(worker, task)
            except Empty:
                n += 1
                if n > 1000:
                    self.logger.debug("[*] No worker or unfinished task")
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
                    self.logger.debug("[*] No finished task")
                    sleep(1)
                    n = 0

    def sendTask(self, worker: Worker, task: Task):
        message = {"appID": task.appID, "dataID": task.dataID}
        messageEncrypted = Message.encrypt(message)
        self.sio.emit(
            'task',
            to=worker.taskSocketID,
            data=messageEncrypted,
            namespace='/task')
        self.logger.debug("Sent task %d", task.taskID)

    def sendResult(self, task: Task):
        user = self.registry.users[task.userID]
        message = {"appID": task.dataID, "dataID": task.resultID}
        messageEncrypted = Message.encrypt(message)
        self.sio.emit(
            'result',
            to=user.socketID,
            data=messageEncrypted,
            namespace='/task')
        self.logger.debug("Sent result %d", task.taskID)


class TaskNamespace(socketio.Namespace):

    def __init__(self, namespace=None, taskManager: TaskManager = None,
                 registry: Registry = None,
                 sio: socketio.Server = None,
                 dataManager: DataManager = None,
                 logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.taskManager: TaskManager = taskManager
        self.registry: Registry = registry
        self.sio: socketio.Server = sio
        self.coordinator = Coordinator(taskManager=self.taskManager,
                                       registry=self.registry,
                                       sio=self.sio,
                                       dataManager=dataManager,
                                       logLevel=logLevel)
        self.logger = get_logger("TaskNamespace", logLevel)

        self.coordinator.run()

    def on_register(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        if "role" not in messageDecrypted:
            return
        role = messageDecrypted["role"]

        if role == 'user':
            userID = messageDecrypted["userID"]
            self.registry.updateUserTaskSocketID(userID=userID, socketID=socketID)
            message = {'userID': userID}
            messageEncrypted = Message.encrypt(message)
            user = self.registry.users[userID]
            self.emit('registered', room=user.taskSocketID, data=messageEncrypted)

        elif role == 'worker':
            workerID = messageDecrypted["workerID"]
            self.registry.updateWorkerTaskSocketID(workerID=workerID, socketID=socketID)
            message = {'workerID': workerID}
            messageEncrypted = Message.encrypt(message)
            worker = self.registry.workers[workerID]
            self.sio.emit('registered', room=worker.taskSocketID, data=messageEncrypted)

    def on_submit(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        userID = messageDecrypted["userID"]
        if not socketID == self.registry.users[userID].taskSocketID:
            return

        appID = messageDecrypted["appID"]
        dataID = messageDecrypted["dataID"]
        taskID = self.taskManager.submit(userID, appID, dataID)

        message = {'taskID': taskID, 'appID': appID, 'dataID': dataID}
        messageEncrypted = Message.encrypt(message)
        self.sio.emit("submitted", to=socketID,
                      data=messageEncrypted, namespace='/task')
        self.logger.info("[*] Received Task-%d from User-%d", taskID, userID)

    def on_finish(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        workerID = messageDecrypted['workerID']

        if not socketID == self.registry.workers[workerID].taskSocketID:
            return

        taskID = messageDecrypted['taskID']
        task = self.taskManager.processingTasks[taskID]

        if not workerID == task.workerID:
            return

        dataID = messageDecrypted["dataID"]
        resultID = messageDecrypted["resultID"]
        self.taskManager.finish(taskID, resultID)
        self.notify(dataID, resultID)
        self.logger.debug("Received Finished Task-%d, dataID: %d, resultID: %d", taskID, dataID, resultID)

    def notify(self, dataID, resultID):
        pass
