import socketio
import logging

from logger import get_logger
from datatype import Worker, NodeSpecs, Task
from registry import Registry
from message import Message


class TaskManager:

    def __init__(self, registry: Registry = None):
        self.currentTaskID = 0
        self.tasks: {Task} = {}
        self.registry = registry

    def submit(self, userID, inputData):
        self.currentTaskID += 1
        self.tasks[self.currentTaskID] = Task(
            taskID=self.currentTaskID, userID=userID, inputData=inputData)
        return self.currentTaskID

    def finish(self, userID: int, taskID, outputData):
        if self.tasks[taskID].userID == userID:
            self.tasks[taskID].outputData = outputData
            self.tasks[taskID].hasDone = True


class TaskNamespace(socketio.Namespace):

    def __init__(self, namespace=None, taskManager: TaskManager = None,
                 sio=None, logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.taskManager = taskManager
        self.registry = self.taskManager.registry
        self.logger = get_logger("TaskNamespace", logLevel)
        self.sio = sio

    def on_submit(self, socketID, data):
        msg = Message.decrypt(data)
        userID = msg["userID"]
        inputData = msg["inputData"]

        taskID = self.taskManager.submit(userID, inputData)
        self.sio.emit("taskReceived", to=socketID,
                      data=taskID, namespace='/task')
        self.logger.info("[*] taskReceived: %d.", taskID)

    def on_finish(self, socketID, data):
        msg = Message.decrypt(data)
        userID = msg["userID"]
        taskID = msg["taskID"]
        outData = msg["outData"]
        task = self.taskManager.tasks[taskID]
        if task.userID == userID and userID == self.registry.workersBySocketID[socketID].userID:
            task.outData = outData
            task.hasDone = True
