import socketio
import logging

from logger import get_logger
from datatype import Worker, NodeSpecs, Task
from message import Message


class TaskManager:

    def __init__(self):
        self.id = 0
        self.tasks = {}

    def addTask(self, userID, inputData):
        self.id += 1
        self.tasks[self.id] = Task(
            taskID=self.id, userID=userID, inputData=inputData)
        return self.id


class TaskNamespace(socketio.Namespace):

    def __init__(self, namespace=None, taskManager: TaskManager = None,
                 sio=None, logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.taskManager = taskManager
        self.logger = get_logger("Registry", logLevel)
        self.sio = sio

    def on_add_task(self, userID: int, socketID: str, msg):
        taskID = self.taskManager.addTask(userID, msg)
        self.sio.emit("taskReceived",  to=socketID,
                      data=taskID, namespace='/task')
        self.logger.info("[*] taskReceived: %d." % taskID)

    def on_finishTask(self, data):
        frame = Message.decrypt(data)
        cv2.imshow('cam', frame)  # show the frame
        cv2.waitKey(0)
        cv2.destroyAllWindows()

