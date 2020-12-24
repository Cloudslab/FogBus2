import logging
import socketio

from logger import get_logger
from registry import Registry
from message import Message
from dataManager import DataManager
from taskManager import TaskManager


class TaskNamespace(socketio.Namespace):

    def __init__(self, namespace=None, taskManager: TaskManager = None,
                 registry: Registry = None,
                 sio: socketio.Server = None,
                 logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.taskManager: TaskManager = taskManager
        self.registry: Registry = registry
        self.sio: socketio.Server = sio
        self.logger = get_logger("TaskNamespace", logLevel)

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
            self.emit('registered', room=worker.taskSocketID, data=messageEncrypted)

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
