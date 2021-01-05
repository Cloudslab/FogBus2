import logging
import socketio

from logger import get_logger
from masterSideRegistry import Registry
from message import Message
from taskManager import TaskManager
from datatype import Task
from queue import Empty


class TaskNamespace(socketio.Namespace):

    def __init__(self, namespace=None, taskManager: TaskManager = None,
                 registry: Registry = None,
                 logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.taskManager: TaskManager = taskManager
        self.registry: Registry = registry
        self.logger = get_logger("TaskNamespace", logLevel)

    def on_register(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        if "role" not in messageDecrypted:
            return
        role = messageDecrypted["role"]

        if role == 'user':
            userID = messageDecrypted["userID"]
            user = self.registry.users[userID]
            user.taskSocketID = socketID
            message = {'userID': userID}
            messageEncrypted = Message.encrypt(message)
            self.emit('registered', room=user.taskSocketID, data=messageEncrypted)

        elif role == 'worker':
            workerID = messageDecrypted["workerID"]
            worker = self.registry.workers[workerID]
            worker.taskSocketID = socketID
            message = {'workerID': workerID}
            messageEncrypted = Message.encrypt(message)
            self.emit('registered', room=worker.taskSocketID, data=messageEncrypted)

    def on_submit(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        userID = messageDecrypted["userID"]
        if not socketID == self.registry.users[userID].taskSocketID:
            return

        appID = messageDecrypted["appID"]
        dataID = messageDecrypted["dataID"]
        try:
            worker = self.registry.waitingWorkers.get(block=False)
            task = Task(
                workerID=worker.workerID,
                userID=userID,
                taskID=1,
                appID=appID,
                dataID=dataID)
            self.taskManager.processingTasks[task.taskID] = task
            message = {"taskID": task.taskID, "appID": task.appID, "dataID": task.dataID}
            messageEncrypted = Message.encrypt(message)
            self.emit(
                'task',
                room=worker.taskSocketID,
                data=messageEncrypted,
                callback=self.sendResult
            )
            self.logger.debug("Sent Task-%d to Worker-%d", task.taskID, worker.workerID)
            message = {'isHandling': True,
                       'taskID': task.taskID,
                       'appID': task.appID,
                       'dataID': task.dataID}
            return Message.encrypt(message)
        except Empty:
            message = {'isHandling': False,
                       'reason': 'No worker now',
                       'appID': appID,
                       'dataID': dataID}
            return Message.encrypt(message)

    def sendResult(self, message):
        messageDecrypted = Message.decrypt(message)
        taskID = messageDecrypted['taskID']
        task = self.taskManager.processingTasks[taskID]
        user = self.registry.users[task.userID]
        messageEncrypted = Message.encrypt(messageDecrypted)
        worker = self.registry.workers[task.workerID]
        self.registry.waitingWorkers.put(worker)
        self.emit('result',
                  room=user.taskSocketID,
                  data=messageEncrypted)
        self.logger.debug("Sent result of Task-%d to User-%d", task.taskID, task.userID)
