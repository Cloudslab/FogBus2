import logging
from queue import Queue
from logger import get_logger
from datatype import Task
from typing import NoReturn


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
