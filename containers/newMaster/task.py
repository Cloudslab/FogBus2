import logging
import threading
import socketio

from time import sleep
from queue import Queue, Empty
from logger import get_logger
from datatype import Task
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

    def submit(self, appID, dataID):
        # TODO: racing
        self.currentTaskID += 1
        taskID = self.currentTaskID
        self.waitingTasks.put(
            Task(
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
                self.sendTask(worker.workerID, task.inputData)
                self.logger.debug("sent task %d", task.taskID)
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
                self.sendResult(task.userID, task.outputData)
                self.logger.debug("sent result %d", task.taskID)
            except Empty:
                n += 1
                if n > 1000:
                    self.logger.debug("[*] No finished task")
                    sleep(1)
                    n = 0

    def sendTask(self, workerID: int, inputData: str):
        socketID = self.registry.workersByWorkerID[workerID]
        self.sio.emit(
            'task',
            to=socketID,
            data=Message.encrypt(inputData),
            namespace='/task')

    def sendResult(self, userID: int, outData):
        socketID = self.registry.usersByUserID[userID].socketID
        self.sio.emit(
            'result',
            to=socketID,
            data=Message.encrypt(outData),
            namespace='/task')


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

    def on_submit(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        appID = messageDecrypted["appID"]
        dataID = messageDecrypted["dataID"]

        taskID = self.taskManager.submit(appID, dataID)

        message = {'taskID': taskID, 'appID': appID, 'dataID': dataID}
        messageEncrypted = Message.encrypt(message)
        self.sio.emit("submitted", to=socketID,
                      data=messageEncrypted, namespace='/task')
        self.logger.info("[*] Received Task: %d.", taskID)

    def on_finish(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        taskID = messageDecrypted["taskID"]
        dataID = messageDecrypted["dataID"]
        resultID = messageDecrypted["resultID"]

        if taskID not in self.taskManager.processingTasks[taskID]:
            return

        task = self.taskManager.processingTasks[taskID]
        workerID = self.registry.workersBySocketID[socketID].workerID

        if not workerID == task.workerID:
            return
        self.taskManager.finish(taskID, resultID)
        self.notify(dataID, resultID)
        self.logger.debug("Received Finished Task-%d, dataID: %d, resultID: %d", taskID, dataID, resultID)

    def notify(self, dataID, resultID):
        pass
